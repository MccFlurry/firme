"""Customer confirmation lifecycle: create, respond, expire and reevaluate."""

import secrets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app import store
from app.services import evaluate_and_store
from contracts.types import Confirmation, Event, Sale
from engine.rules import load_config

EVENT_DETAILS = {
    "confirmada": "El cliente confirmó que la oferta es lo que acordó.",
    "corregida": "El cliente pidió corregir algo de la oferta.",
    "desconocida": "El cliente no reconoció este servicio.",
    "silencio": "Ventana de confirmación vencida sin respuesta (simulado).",
}


def _clock() -> datetime:
    return datetime.now(ZoneInfo(load_config("settings")["timezone"]))


def _window_hours() -> int:
    return load_config("settings")["confirmation_window_hours"]


def get(sale_id: str) -> Confirmation | None:
    state = store.load()
    if sale_id not in state["sales"]:
        raise KeyError(sale_id)
    confirmation = state["confirmations"].get(sale_id)
    return Confirmation.model_validate(confirmation) if confirmation else None


def find_by_token(token: str) -> tuple[str | None, Confirmation | None]:
    state = store.load()
    for sale_id, item in state["confirmations"].items():
        if item.get("token") == token:
            return sale_id, Confirmation.model_validate(item)
    return None, None


def create(sale_id: str) -> Confirmation:
    def work(data):
        if sale_id not in data["sales"]:
            raise KeyError(sale_id)
        at = _clock()
        confirmation = Confirmation(
            sale_id=sale_id,
            token=secrets.token_urlsafe(8),
            status="pendiente",
            created_at=at.isoformat(),
            expires_at=(at + timedelta(hours=_window_hours())).isoformat(),
        )
        data["confirmations"][sale_id] = confirmation.model_dump(mode="json")
        data["events"].append(Event(
            sale_id=sale_id, at=at.isoformat(), kind="enlace_generado",
            detail="Enlace de confirmación generado para el cliente.",
        ).model_dump())
        return confirmation

    return store.update(work)


def _mark(sale_id: str, status: str, note: str | None = None) -> Confirmation:
    def work(data):
        if sale_id not in data["sales"]:
            raise KeyError(sale_id)
        confirmation = Confirmation.model_validate(data["confirmations"][sale_id])
        confirmation.status = status
        confirmation.note = note
        confirmation.responded_at = _clock().isoformat()
        data["confirmations"][sale_id] = confirmation.model_dump(mode="json")
        detail = EVENT_DETAILS.get(status, "El cliente respondió a la confirmación.")
        if note:
            detail = f"{detail} Nota: {note}"
        data["events"].append(Event(
            sale_id=sale_id, at=_clock().isoformat(), kind=status, detail=detail,
        ).model_dump())
        return confirmation

    return store.update(work)


def respond(token: str, status: str, note: str | None = None) -> Confirmation:
    sale_id, _ = find_by_token(token)
    if sale_id is None:
        raise KeyError(token)
    confirmation = _mark(sale_id, status, note)
    sale = Sale.model_validate(store.load()["sales"][sale_id])
    evaluate_and_store(sale)
    return confirmation


def expire(sale_id: str) -> Confirmation:
    def work(data):
        if sale_id not in data["sales"]:
            raise KeyError(sale_id)
        item = data["confirmations"].get(sale_id)
        at = _clock()
        confirmation = Confirmation.model_validate(item) if item else Confirmation(
            sale_id=sale_id,
            token=secrets.token_urlsafe(8),
            status="silencio",
            created_at=at.isoformat(),
            expires_at=at.isoformat(),
        )
        confirmation.status = "silencio"
        confirmation.responded_at = at.isoformat()
        data["confirmations"][sale_id] = confirmation.model_dump(mode="json")
        data["events"].append(Event(
            sale_id=sale_id, at=at.isoformat(), kind="silencio",
            detail=EVENT_DETAILS["silencio"],
        ).model_dump())
        return confirmation

    store.update(work)
    sale = Sale.model_validate(store.load()["sales"][sale_id])
    evaluate_and_store(sale)
    return Confirmation.model_validate(store.load()["confirmations"][sale_id])
