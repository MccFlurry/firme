"""Shared evaluation and persistence for sales and customer confirmation."""

import secrets
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from app import store
from contracts.types import Confirmation, Context, Event, FieldEdit, Sale, Verdict
from engine import evaluate
from engine import llm
from engine.llm import normalize_promise
from engine.rules import load_config

_EXPLANATION_LOCK = threading.Lock()


def verdict_explanation(sale: Sale, verdict: Verdict) -> dict:
    signature = {"expected_cost": verdict.expected_cost, "decision": verdict.decision,
                 "evidence": [item.model_dump(mode="json") for item in verdict.evidence],
                 "enabled": llm.describe()["provider"] != "determinista"}
    # ponytail: one explanation at a time; per-sale locks if concurrent viewing grows.
    with _EXPLANATION_LOCK:
        cached = store.load().get("explanations", {}).get(sale.id, {})
        if cached.get("signature") == signature:
            return cached
        text = llm.explain_verdict(sale, verdict)
        result = {"signature": signature, "text": text, **llm.describe()}

        def persist(data):
            current = data["verdicts"].get(sale.id, {})
            if all(current.get(key) == signature[key] for key in ("expected_cost", "decision", "evidence")):
                data.setdefault("explanations", {})[sale.id] = result

        store.update(persist)
        return result


def evaluate_and_store(sale: Sale, history: list[Sale] | None = None) -> Verdict:
    """Return the saved verdict; an empty sale ID allocates a new V-XXXX ID.

    Keep an unchanged normalized promise when T4 reevaluates a confirmation.
    History, confirmation, edits and writes share the store's process lock.
    """
    sale = sale.model_copy(deep=True)
    if sale.promise_text and (
        sale.promise is None or sale.promise.raw_text != sale.promise_text
    ):
        sale.promise, _ = normalize_promise(sale.promise_text, load_config("catalog"))
    elif not sale.promise_text and sale.promise and sale.promise.raw_text:
        sale.promise = None

    def persist(data):
        if not sale.id:
            while not sale.id or sale.id in data["sales"]:
                sale.id = f"V-{secrets.token_hex(2).upper()}"
        now = datetime.now(ZoneInfo(load_config("settings")["timezone"])).isoformat()
        previous = data["sales"].get(sale.id)
        changes = []
        if previous:
            saved = Sale.model_validate(previous)
            sale.edits = saved.edits.copy()
            for field in Sale.model_fields:
                if field in {"id", "promise", "edits"}:
                    continue
                old, new = getattr(saved, field), getattr(sale, field)
                if old != new:
                    changes.append(field)
                    sale.edits.append(FieldEdit(
                        field=field, at=now,
                        old=str(old) if old is not None else None,
                        new=str(new) if new is not None else None,
                    ))
        confirmation = data["confirmations"].get(sale.id)
        verdict = evaluate(sale, Context(
            history=history if history is not None else [
                Sale.model_validate(item) for key, item in data["sales"].items() if key != sale.id
            ],
            confirmation=Confirmation.model_validate(confirmation) if confirmation else None,
            now=now,
        ))
        sale.promise = verdict.promise
        if not previous:
            data["events"].append(Event(
                sale_id=sale.id, at=now, kind="registrada", detail="Venta simulada registrada."
            ).model_dump())
        elif changes:
            data["events"].append(Event(
                sale_id=sale.id, at=now, kind="editada",
                detail=f"Cambios registrados: {len(changes)}. Consulta el detalle de cambios."
            ).model_dump())
        result = verdict.model_dump(mode="json")
        if data["verdicts"].get(sale.id) != result:
            data["alerts_done"] = [key for key in data["alerts_done"] if key != sale.id]
        data["sales"][sale.id] = sale.model_dump(mode="json")
        data["verdicts"][sale.id] = result
        data["events"].append(Event(
            sale_id=sale.id, at=now, kind="evaluada",
            detail=f"{verdict.decision} · Costo esperado S/ {verdict.expected_cost:.2f}."
        ).model_dump())
        return verdict

    return store.update(persist)
