"""Normalize sale values and derive comparators without inventing missing data."""

import math
import re
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from contracts.types import Context, Promise, Sale
from engine.rules import load_config


def normalize(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "").casefold()
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^\w\s]|_", " ", text).split())


def catalog_key(value: str | None, items: dict) -> str | None:
    if not value or not value.strip():
        return None
    for key, item in items.items():
        if normalize(value) in {normalize(alias) for alias in [key, item.get("name", key), *item.get("aliases", [])]}:
            return key
    return value.strip()


def parse_datetime(value: str | None, settings: dict) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
        zone = ZoneInfo(settings["timezone"])
        return parsed.replace(tzinfo=zone) if parsed.tzinfo is None else parsed.astimezone(zone)
    except (TypeError, ValueError, OverflowError):
        return None


def current_time(ctx: Context, settings: dict) -> datetime:
    return parse_datetime(ctx.now, settings) or datetime.now(ZoneInfo(settings["timezone"]))


def number(value) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError, OverflowError):
        return None


def supported_price(plan: dict, promo: dict, applies: bool | None) -> float | None:
    price = plan.get("price")
    if price is not None and applies:
        price -= promo.get("discount", 0)
    return price


def build_facts(sale: Sale, ctx: Context, catalog: dict, settings=None, costs=None) -> dict:
    settings = settings if settings is not None else load_config("settings")
    costs = costs if costs is not None else load_config("costs")
    facts = sale.model_dump(exclude={"promise", "edits", "extra"})
    facts.update({key: value if not isinstance(value, str) or value.strip() else None for key, value in facts.items()})
    facts["price"] = number(sale.price)
    plans, promos = catalog["plans"], catalog["promos"]
    plan_id = catalog_key(sale.plan, plans)
    promo_id = catalog_key(sale.promo, promos)
    plan, promo = plans.get(plan_id, {}), promos.get(promo_id, {})
    promo_applies = plan_id in promo.get("applies_to", []) if plan_id and promo_id else None
    promise = sale.promise or Promise()
    promise_plan = catalog_key(promise.plan, plans)
    promise_promo = catalog_key(promise.promo, promos)
    offered_plan, offered_promo = plans.get(promise_plan, {}), promos.get(promise_promo, {})
    promise_promo_applies = promise_plan in offered_promo.get("applies_to", []) if promise_plan and promise_promo else None
    district = catalog_key(sale.district, catalog["coverage"])
    zone = catalog["coverage"].get(district, {})
    registered = parse_datetime(sale.registered_at, settings)
    installation = parse_datetime(sale.install_date, settings)
    confirmation = ctx.confirmation if ctx.confirmation and ctx.confirmation.sale_id == sale.id else None
    lexicon = load_config("lexicon")
    unsupported = [item["text"] for item in lexicon["claims"]
                   if item["status"] in {"inexistente", "insostenible"}
                   and any(normalize(claim) in {normalize(alias) for alias in [item["text"], *item["aliases"]]}
                           for claim in promise.claims)]
    facts.update(
        plan=plan_id, promo=promo_id, district=district, plan_exists=plan_id in plans,
        catalog_price=supported_price(plan, promo, promo_applies), catalog_speed=plan.get("speed_mbps"),
        catalog_speeds=[item["speed_mbps"] for item in plans.values()], promo_applies=promo_applies,
        zone_max_speed=zone.get("max_speed_mbps"),
        zone_supports_plan=(plan["tech"] in zone.get("tech", []) and plan["speed_mbps"] <= zone.get("max_speed_mbps", 0))
        if plan and district else None,
        install_within_window=(0 <= (installation - registered).total_seconds() <= settings["install_window_hours"] * 3600)
        if installation and registered else None,
        registered_install_days=(installation.date() - registered.date()).days if installation and registered else None,
        window_install_date=(registered + timedelta(hours=settings["install_window_hours"])).isoformat() if registered else None,
        hour=registered.hour if registered else None,
        consent_missing=not bool(sale.consent_evidence and sale.consent_evidence.strip()),
        confirmation_status=confirmation.status if confirmation else None,
        confirmation_note=confirmation.note if confirmation else None,
        promise_plan=promise_plan, promise_plan_exists=promise_plan in plans,
        promise_price=number(promise.price), promise_speed_mbps=promise.speed_mbps,
        promise_catalog_speed=offered_plan.get("speed_mbps"), promise_promo=promise_promo,
        promise_promo_applies=promise_promo_applies,
        promise_catalog_price=supported_price(offered_plan, offered_promo, promise_promo_applies),
        promise_install_days=promise.install_days,
        promise_install_date=(registered + timedelta(days=promise.install_days)).isoformat()
        if registered and promise.install_days is not None else None,
        unsupported_claims=unsupported, billing_amount=number(sale.extra.get("billing_amount")),
        price_tolerance=catalog["price_tolerance"],
        prior=costs["priors"].get(sale.channel, costs["priors"]["default"]),
    )
    for key in ("burst_threshold", "fill_seconds_threshold", "night_start_hour", "night_end_hour",
                "price_edits_threshold", "identity_edits_threshold", "contact_collisions_threshold",
                "address_collisions_threshold", "cohort_prior_threshold"):
        facts[key] = settings[key]
    facts["price_edits"] = sum(edit.field == "price" for edit in sale.edits)
    facts["identity_edits"] = sum(
        edit.field in {"customer_name", "customer_doc"} and edited is not None and edited > registered
        for edit in sale.edits if registered and (edited := parse_datetime(edit.at, settings))
    ) if registered else None
    history = {other.id: other for other in ctx.history if other.id != sale.id}.values()
    facts["burst_count"] = 1 + sum(
        other.seller_id == sale.seller_id and 0 <= (registered - stamp).total_seconds() <= settings["burst_window_minutes"] * 60
        for other in history if (stamp := parse_datetime(other.registered_at, settings))
    ) if registered and sale.seller_id else None
    for field, key in (("phone", "phone_collisions"), ("email", "email_collisions"), ("customer_doc", "doc_collisions")):
        def contact(value):
            return re.sub(r"\D", "", value or "") if field == "phone" else (value or "").strip().casefold()

        value = contact(getattr(sale, field))
        facts[key] = sum(contact(getattr(other, field)) == value and bool(normalize(other.customer_name))
                         and normalize(other.customer_name) != normalize(sale.customer_name) for other in history)
        if not value or not normalize(sale.customer_name):
            facts[key] = None
    facts["address_collisions"] = sum(
        normalize(other.address) == normalize(sale.address) and stamp.date() == registered.date()
        for other in history if (stamp := parse_datetime(other.registered_at, settings))
    ) if normalize(sale.address) and registered else None
    return facts
