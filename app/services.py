"""Shared evaluation and persistence for sales and customer confirmation."""

import secrets
from datetime import datetime
from zoneinfo import ZoneInfo

from app import store
from contracts.types import Confirmation, Context, Event, FieldEdit, Sale, Verdict
from engine import evaluate
from engine.llm import normalize_promise
from engine.rules import load_config


def evaluate_and_store(sale: Sale) -> Verdict:
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
            history=[Sale.model_validate(item) for key, item in data["sales"].items() if key != sale.id],
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
