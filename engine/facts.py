"""Normalize sale values and derive comparators without inventing missing data."""

import math
import re
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from contracts.types import Context, Promise, Sale
from engine.rules import load_config

CONFIRMATION_STATES = {
    "confirmada": "confirmada", "negada": "desconocida", "enviada": "pendiente",
    "no_respondida": "silencio", "confirmada_con_correccion": "corregida", "no_enviada": None,
}


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
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError, OverflowError):
        return None


def plan_for_speed(value, plans: dict) -> str | None:
    speed = number(value)
    if speed is None:
        return None
    return next((key for key, plan in plans.items() if plan["speed_mbps"] == speed), f"{speed:g} Mbps")


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
    plan_id = catalog_key(sale.plan, plans) or plan_for_speed(sale.extra.get("velocidad_contratada"), plans)
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
    status = confirmation.status if confirmation else CONFIRMATION_STATES.get(str(sale.extra.get("confirmacion_titular")))
    confirmation_ts = confirmation.responded_at if confirmation else sale.extra.get("confirmacion_titular_ts")
    responded = parse_datetime(confirmation_ts, settings)
    for key in ("plazo_vigencia", "forma_entrega_recibo", "tenencia", "nombre_condominio", "torre",
                "departamento", "catalogo_referencia_id", "equipo"):
        facts[key] = normalize(str(sale.extra.get(key) or "")) or None
    for key in ("velocidad_contratada", "cargo_instalacion_costo", "cargo_instalacion_cuotas",
                "score_crediticio", "plazo_estimado_instalacion"):
        facts[key] = number(sale.extra.get(key))
    text = normalize(sale.promise_text or promise.raw_text)
    claims_text = " ".join(normalize(claim) for claim in promise.claims)
    address = normalize(f"{sale.address or ''} {sale.district or ''}")
    region = next((key for key, cities in catalog["regions"].items()
                   if any(f" {normalize(city)} " in f" {address} " for city in cities)), None)
    reference = sale.extra.get("catalogo_referencia_id")
    reference = reference.strip() or None if isinstance(reference, str) else None

    def reference_price(item, item_id, recorded_price, promotion, applies):
        promo_price = catalog["promo_prices"].get(item_id, {}).get("price")
        if promo_price is not None and recorded_price == promo_price:
            return promo_price
        if reference in item.get("surface_prices", {}):
            return item["surface_prices"][reference]
        # No price assertion against a web-only plan without its governing surface.
        if item and "cartilla" not in item.get("surfaces", []) and reference not in item["surfaces"]:
            return None
        return supported_price(item, promotion, applies)

    web_only = [item["speed_mbps"] for item in plans.values() if "cartilla" not in item["surfaces"]]
    lexicon = load_config("lexicon")
    unsupported = [item["text"] for item in lexicon["claims"]
                   if item["status"] in {"inexistente", "insostenible"}
                   and any(normalize(claim) in {normalize(alias) for alias in [item["text"], *item["aliases"]]}
                           for claim in promise.claims)]
    known_claims = {normalize(alias) for item in lexicon["claims"] for alias in [item["text"], *item["aliases"]]}
    if promise.source == "llm":
        unsupported.extend({"text": claim, "origen": "IA"} for claim in dict.fromkeys(promise.claims)
                           if normalize(claim) and not any(f" {alias} " in f" {normalize(claim)} "
                                                          for alias in known_claims))
    facts.update(
        plan=plan_id, promo=promo_id, district=district, plan_exists=plan_id in plans,
        catalog_price=reference_price(plan, plan_id, sale.price, promo, promo_applies), catalog_speed=plan.get("speed_mbps"),
        catalog_speeds=[item["speed_mbps"] for item in plans.values()], promo_applies=promo_applies,
        zone_max_speed=zone.get("max_speed_mbps"),
        zone_supports_plan=(plan["tech"] in zone.get("tech", []) and plan["speed_mbps"] <= zone.get("max_speed_mbps", 0))
        if plan and district else None,
        install_within_window=(0 <= (installation - registered).total_seconds() <= settings["install_ceiling_days"] * 86400)
        if installation and registered else (0 <= facts["plazo_estimado_instalacion"] <= settings["install_ceiling_days"])
        if facts["plazo_estimado_instalacion"] is not None else None,
        registered_install_days=(installation.date() - registered.date()).days if installation and registered else None,
        window_install_date=(registered + timedelta(days=settings["install_ceiling_days"])).isoformat() if registered else None,
        hour=registered.hour if registered else None,
        consent_missing=not bool(sale.consent_evidence and sale.consent_evidence.strip())
        and not sale.extra.get("consent_not_in_source"),
        confirmation_status=status, confirmation_ts=confirmation_ts,
        confirmation_late=bool(status == "confirmada" and registered and responded
                               and responded > registered + timedelta(days=settings["verification_window_days"])),
        verification_window_days=settings["verification_window_days"],
        confirmation_note=confirmation.note if confirmation else None,
        promise_plan=promise_plan, promise_plan_exists=promise_plan in plans,
        promise_price=number(promise.price), promise_speed_mbps=promise.speed_mbps,
        promise_catalog_speed=offered_plan.get("speed_mbps"), promise_promo=promise_promo,
        promise_promo_applies=promise_promo_applies,
        promise_catalog_price=reference_price(offered_plan, promise_plan, promise.price, offered_promo, promise_promo_applies),
        promise_install_days=promise.install_days,
        promise_install_date=(registered + timedelta(days=promise.install_days)).isoformat()
        if registered and promise.install_days is not None else None,
        unsupported_claims=unsupported, billing_amount=number(sale.extra.get("billing_amount")),
        price_tolerance=catalog["price_tolerance"],
        prior=max(costs["priors"].get(sale.channel, costs["priors"]["default"]),
                  costs["priors_by_seller"].get(sale.seller_id, 0),
                  costs["priors_by_team"].get(str(sale.extra.get("equipo")), 0)),
        promise_no_term=any(normalize(alias) in text or normalize(alias) in claims_text for item in lexicon["claims"]
                            if item["text"] == "sin contrato" for alias in item["aliases"]),
        promise_mentions_recibo="recibo" in text,
        promise_mentions_installation_fee=bool(re.search(r"\b(?:cuotas?|instalacion)\b", text)),
        promise_all_inclusive="todo incluido" in text,
        promise_promo_duration=bool(re.search(r"promocional|por \d+ meses|despues sube|luego sube", text)),
        catalog_ambiguous=not reference and (facts["velocidad_contratada"] in web_only
                                           or plan.get("speed_mbps") in web_only or promise.speed_mbps in web_only
                                           or offered_plan.get("speed_mbps") in web_only),
        address_region=region, plan_zones=plan.get("zones", []),
        min_credit_score=catalog["min_credit_score"]["value"],
        paper_invoice_fee=catalog["paper_invoice_fee"]["amount"],
        installation_quota=catalog["installation"]["quota"],
        consent_evidence=sale.consent_evidence,
    )
    facts["expected_monthly_total"] = (sale.price + catalog["paper_invoice_fee"]["amount"]
                                       if sale.price is not None else None)
    lexical = [item for item in lexicon["claims"] if item["text"] in unsupported]
    facts["unsupported_claim_source"] = "; ".join(item["fuente"] for item in lexical)
    facts["unsupported_claim_origin"] = "PUBLICO" if lexical and len(lexical) == len(unsupported) and all(
        item["origen"] == "PUBLICO" for item in lexical) else "SUPUESTO_DEMO"
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
        facts[key] = sum(contact(getattr(other, field)) == value and any(
            normalize(getattr(sale, identity)) and normalize(getattr(other, identity))
            and normalize(getattr(sale, identity)) != normalize(getattr(other, identity))
            for identity in ("customer_name", "customer_doc", "address")) for other in history)
        if not value:
            facts[key] = None
    facts["address_collisions"] = sum(
        normalize(other.address) == normalize(sale.address) and stamp.date() == registered.date()
        for other in history if (stamp := parse_datetime(other.registered_at, settings))
    ) if normalize(sale.address) and registered else None
    return facts
