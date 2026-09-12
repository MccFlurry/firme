"""WIN's mobile-first sale, verdict and alert screens."""

import json
import re
import math
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from app import store
from app.services import evaluate_and_store, verdict_explanation
from contracts.types import Event, Sale, Verdict
from engine import llm
from engine.ingest import parse
from engine.facts import CONFIRMATION_STATES
from engine.rules import load_config

APP_DIR = Path(__file__).resolve().parent
app = FastAPI(title="WIN · Calidad de venta", docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

FIELD_LABELS = {
    "seller_id": "Código del vendedor", "channel": "Canal", "customer_name": "Nombre del cliente",
    "customer_doc": "Documento", "phone": "Teléfono", "email": "Correo electrónico",
    "address": "Dirección", "district": "Distrito", "plan": "Plan", "price": "Precio mensual (S/)",
    "promo": "Promoción", "install_date": "Instalación prevista", "registered_at": "Fecha y hora de registro",
    "fill_seconds": "Tiempo de llenado (segundos)", "consent_evidence": "Evidencia de consentimiento",
    "promise_text": "Lo que se ofreció al cliente", "label": "Etiqueta de demostración", "extra": "Datos adicionales",
    "promise": "Promesa", "extra.billing_amount": "Monto a facturar", "speed_mbps": "Velocidad (Mbps)",
    "install_days": "Plazo de instalación (días)", "claims": "Afirmaciones detectadas",
    "raw_text": "Texto original", "source": "Método de extracción",
}
FORM_FIELDS = tuple(field for field in FIELD_LABELS if field in Sale.model_fields and field != "promise")
CHANNEL_LABELS = {"call_center": "Centro de llamadas", "campo": "Campo", "web": "Web", "tienda": "Tienda"}
STRENGTH_LABELS = {"determinista": "Determinista", "estadistica": "Estadística", "linguistica": "Lingüística"}
EVENT_LABELS = {
    "registrada": "Venta registrada", "evaluada": "Venta evaluada", "editada": "Venta editada",
    "aviso": "Aviso atendido", "enlace_generado": "Enlace generado", "confirmada": "Oferta confirmada",
    "corregida": "Corrección solicitada", "desconocida": "Servicio no reconocido", "silencio": "Sin respuesta",
}
templates.env.globals.update(field_labels=FIELD_LABELS, strength_labels=STRENGTH_LABELS, event_labels=EVENT_LABELS)
DECISION_LABELS = {"APROBAR": "pasa", "REVISAR": "revisar", "RETENER": "revisar (prioridad máxima)",
                   "ABSTENERSE": "abstención"}
CONFIRMATION_LABELS = {"no_enviada": "No enviada", "enviada": "Pendiente", "no_respondida": "Sin respuesta",
                       "confirmada": "Confirmada", "confirmada_con_correccion": "Corrección solicitada",
                       "negada": "Servicio no reconocido"}
templates.env.globals.update(decision_labels=DECISION_LABELS, confirmation_labels=CONFIRMATION_LABELS)
templates.env.filters["plain"] = lambda text: re.sub(r"(?:[Ll]a regla |regla )?\bR\d{2}_[a-z_]+\s*:?\s*", "", "" if text is None else str(text)).replace("_", " ").replace("  ", " ")  # ponytail: hide rule ids and slugs from non-technical readers


def now():
    return datetime.now(ZoneInfo(load_config("settings")["timezone"]))


def format_date(value):
    if not value:
        return "Sin indicar"
    try:
        stamp = datetime.fromisoformat(value)
        if stamp.tzinfo:
            stamp = stamp.astimezone(now().tzinfo)
        return stamp.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return value


templates.env.filters["date_es"] = format_date


def render_form(request, sale=None, values=None, error=None, status_code=200):
    catalog, costs = load_config("catalog"), load_config("costs")
    values = values if values is not None else sale.model_dump() if sale else {}
    values = values.copy()
    for field in ("registered_at", "install_date"):
        if value := values.get(field):
            try:
                stamp = datetime.fromisoformat(value)
                if stamp.tzinfo:
                    stamp = stamp.astimezone(now().tzinfo).replace(tzinfo=None)
                values[field] = stamp.isoformat(timespec="seconds")
            except ValueError:
                pass
    if isinstance(values.get("extra"), dict):
        values["extra"] = json.dumps(values["extra"], ensure_ascii=False, indent=2)
    plan_id, plan = next(iter(catalog["plans"].items()))
    registered = now().replace(microsecond=0)
    example = {
        "seller_id": "VEN-DEMO", "channel": "web", "customer_name": "Cliente de ejemplo",
        "customer_doc": "00000001", "phone": "900000001", "email": "cliente@example.com",
        "address": "Calle Simulada 123", "district": next(iter(catalog["coverage"])),
        "plan": plan_id, "price": plan["price"], "promo": "", "consent_evidence": "firma",
        "registered_at": registered.replace(tzinfo=None).isoformat(),
        "install_date": (registered + timedelta(days=1)).replace(tzinfo=None).isoformat(),
        "promise_text": f"{plan['name']} a S/ {plan['price']:.2f} al mes. Instalación en 1 día.",
        "label": "", "extra": json.dumps({"billing_amount": plan["price"], "simulado": True}),
    }
    return templates.TemplateResponse(request=request, name="home.html", status_code=status_code, context={
        "sale": sale, "values": values, "error": error, "catalog": catalog, "example": example,
        "channels": {key: CHANNEL_LABELS.get(key, key.replace("_", " ").title()) for key in costs["priors"] if key != "default"},
    })


def get_sale(sale_id):
    state = store.load()
    if sale_id not in state["sales"]:
        raise HTTPException(404, "No encontramos esta venta.")
    return Sale.model_validate(state["sales"][sale_id]), state


async def read_sale(request, sale=None):
    # Only the HTML form is ingested here; batch parsing belongs to T3b.
    content_type = request.headers.get("content-type", "").split(";", 1)[0]
    if content_type not in {"", "application/x-www-form-urlencoded", "multipart/form-data"}:
        raise HTTPException(415, "Envía los datos desde el formulario de venta.")
    form = await request.form(max_files=0, max_fields=50)
    values = {field: form.get(field, "") for field in FORM_FIELDS}
    try:
        data = {field: value.strip() or None for field, value in values.items()}
        for field in ("price", "fill_seconds"):
            if data[field] is not None:
                number = float(data[field])
                if not math.isfinite(number) or number < 0 or (field == "fill_seconds" and not number.is_integer()):
                    raise ValueError(f"{FIELD_LABELS[field]} debe ser un número válido mayor o igual a cero.")
                data[field] = int(number) if field == "fill_seconds" else number
        for field in ("registered_at", "install_date"):
            if data[field]:
                stamp = datetime.fromisoformat(data[field])
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=now().tzinfo)
                data[field] = stamp.isoformat()
                if sale and (original := getattr(sale, field)):
                    try:
                        previous = datetime.fromisoformat(original)
                        if previous.tzinfo is None:
                            previous = previous.replace(tzinfo=now().tzinfo)
                        # Native datetime inputs show seconds; keep untouched source precision.
                        if stamp == previous or stamp == previous.replace(microsecond=0):
                            data[field] = original
                    except ValueError:
                        pass
        if not sale and not data["registered_at"]:
            data["registered_at"] = now().isoformat()
        data["extra"] = json.loads(data["extra"]) if data["extra"] else {}
        if not isinstance(data["extra"], dict):
            raise ValueError("Los datos adicionales deben ser un objeto JSON.")
        # Reject NaN/Infinity anywhere in additional data before JSON persistence.
        json.dumps(data["extra"], allow_nan=False)
        candidate = Sale.model_validate((sale.model_dump() if sale else {"id": ""}) | data)
        return candidate, None
    except (ValueError, TypeError, OverflowError, AttributeError) as exc:
        error = "Revisa los números, las fechas y el objeto JSON de datos adicionales."
        if isinstance(exc, ValidationError):
            fields = ", ".join(FIELD_LABELS.get(str(item["loc"][0]), str(item["loc"][0])) for item in exc.errors())
            error = f"Revisa estos campos: {fields}."
        return None, render_form(request, sale, values, error, 422)


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    message = exc.detail if exc.status_code in {404, 415} else "No pudimos procesar la solicitud. Revisa los datos enviados."
    if exc.detail == "Not Found":
        message = "Esta página todavía no está disponible."
    return templates.TemplateResponse(request=request, name="message.html", status_code=exc.status_code,
                                      context={"message": message})


@app.get("/")
def home(request: Request):
    return render_form(request)


@app.post("/ventas")
async def create_sale(request: Request):
    sale, error = await read_sale(request)
    if error is not None:
        return error
    verdict = await run_in_threadpool(evaluate_and_store, sale)
    return RedirectResponse(f"/ventas/{verdict.sale_id}", status_code=303)


@app.get("/ventas/{sale_id}")
def show_verdict(request: Request, sale_id: str):
    sale, state = get_sale(sale_id)
    if sale_id not in state["verdicts"]:
        raise HTTPException(404, "Esta venta todavía no tiene una evaluación.")
    verdict = Verdict.model_validate(state["verdicts"][sale_id])
    explanation = verdict_explanation(sale, verdict)
    confirmation = state["confirmations"].get(sale_id)
    canonical_status = next((key for key, value in CONFIRMATION_STATES.items()
                             if value == confirmation["status"]), None) if confirmation else sale.extra.get("confirmacion_titular")
    return templates.TemplateResponse(request=request, name="verdict.html", context={
        "sale": sale, "verdict": verdict, "costs": load_config("costs"), "catalog": load_config("catalog"),
        "events": [item for item in state["events"] if item["sale_id"] == sale_id],
        "confirmation": confirmation,
        "canonical_status": canonical_status,
        "explanation": explanation,
        "confirmation_url": str(request.base_url) + "c/" + confirmation["token"] if confirmation else None,
    })


@app.get("/ventas/{sale_id}/editar")
def edit_form(request: Request, sale_id: str):
    sale, _ = get_sale(sale_id)
    return render_form(request, sale)


@app.post("/ventas/{sale_id}/editar")
async def edit_sale(request: Request, sale_id: str):
    saved, _ = get_sale(sale_id)
    sale, error = await read_sale(request, saved)
    if error is not None:
        return error
    verdict = await run_in_threadpool(evaluate_and_store, sale)
    return RedirectResponse(f"/ventas/{verdict.sale_id}", status_code=303)


@app.get("/bandeja")
def inbox(request: Request):
    state, groups, clock = store.load(), {}, now()
    verdicts = sorted(state["verdicts"].values(), key=lambda item: item["recoverable_per_minute"], reverse=True)
    for item in verdicts:
        verdict = Verdict.model_validate(item)
        if not verdict.alert or verdict.sale_id in state["alerts_done"]:
            continue
        deadline = datetime.fromisoformat(verdict.alert.deadline)
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=clock.tzinfo)
        minutes = int((deadline - clock).total_seconds() / 60)
        remaining = f"{'Vencido hace' if minutes < 0 else 'Quedan'} {abs(minutes) // 60} h {abs(minutes) % 60} min"
        groups.setdefault(verdict.alert.recipient, []).append({
            "verdict": verdict, "sale": state["sales"][verdict.sale_id], "remaining": remaining, "overdue": minutes < 0,
        })
    return templates.TemplateResponse(request=request, name="inbox.html", context={"groups": groups})


@app.post("/bandeja/{sale_id}/hecho")
def complete_alert(sale_id: str):
    def complete(data):
        if not data["verdicts"].get(sale_id, {}).get("alert"):
            raise HTTPException(404, "No encontramos un aviso para esta venta.")
        if sale_id not in data["alerts_done"]:
            data["alerts_done"].append(sale_id)
            data["events"].append(Event(sale_id=sale_id, at=now().isoformat(), kind="aviso",
                                         detail="Aviso marcado como hecho.").model_dump())
    store.update(complete)
    return RedirectResponse("/bandeja", status_code=303)


@app.get("/salud")
def health():
    provider = llm.describe()
    return {"ok": True, "llm": "configurada" if provider["model"] else "determinista", **provider}


DEMO_PATH = Path(__file__).resolve().parent.parent / "data" / "cases.json"
ADVERSARIAL_PATH = DEMO_PATH.with_name("casos-adversarios.json")
SEVERITY_ORDER = ("baja", "media", "alta", "bloqueante")


def batch_example():
    return [
        {"customer": "Ana Quispe", "phone_number": "912345678", "monthly_price": 99.00,
         "plan_name": "Fibra 200", "label": "buena"},
        {"customer": "Luis Paredes", "phone_number": "923456789", "monthly_price": 40.00,
         "plan_name": "Fibra 300", "label": "mala"},
        {"customer": "Rosa Díaz", "phone_number": "934567890", "monthly_price": 169.00,
         "plan_name": "Fibra 600", "label": "buena"},
        {"customer": "Jorge Salas", "phone_number": "945678901", "monthly_price": 50.00,
         "plan_name": "Fibra 1000", "label": "mala"},
        {"customer": "Mía Castro", "phone_number": "956789012", "monthly_price": 99.00,
         "plan_name": "Fibra 200", "label": "buena"},
    ]


def main_evidence(verdict):
    return next(iter(verdict.evidence), None)


def confusion_matrix(rows):
    tp = fp = tn = fn = abstained = labelled = expected_abstentions = correct_abstentions = 0
    for row in rows:
        verdict, sale = row["verdict"], row["sale"]
        if sale.extra.get("veredicto_esperado") == "abstención":
            expected_abstentions += 1
            correct_abstentions += verdict.decision == "ABSTENERSE"
        if verdict.decision == "ABSTENERSE":
            abstained += 1
            continue
        if sale.label is None:
            continue
        labelled += 1
        positive = verdict.decision in {"REVISAR", "RETENER"}
        if sale.label == "mala" and positive:
            tp += 1
        elif sale.label == "buena" and positive:
            fp += 1
        elif sale.label == "buena":
            tn += 1
        else:
            fn += 1
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "precision": precision,
            "recall": recall, "labelled": labelled, "abstained": abstained,
            "expected_abstentions": expected_abstentions, "correct_abstentions": correct_abstentions}


def render_batch(request, results=None, report=None, confusion=None, error=None, status_code=200, reading=None):
    return templates.TemplateResponse(request=request, name="batch.html", status_code=status_code, context={
        "results": results, "report": report, "confusion": confusion, "error": error,
        "reading": reading,
        "example_json": json.dumps(batch_example(), ensure_ascii=False, indent=2),
        "catalog": load_config("catalog"),
    })


@app.get("/lote")
def batch_form(request: Request):
    return render_batch(request)


@app.post("/lote")
async def batch_submit(request: Request, payload: str = Form(""), file: UploadFile | None = File(None),
                       demo: str = Form("")):
    if demo:
        content, filename = (ADVERSARIAL_PATH if demo == "adversarios" else DEMO_PATH).read_text(encoding="utf-8"), None
    elif file is not None and file.filename:
        content, filename = await file.read(), file.filename
    else:
        content, filename = payload, None
    if not content:
        return render_batch(request, error="Pega un lote JSON/CSV o sube un archivo para procesar.", status_code=400)
    sales, report = await run_in_threadpool(parse, content, filename)
    promises = await run_in_threadpool(
        llm.normalize_promises, [sale.promise_text or "" for sale in sales], load_config("catalog"),
    )
    for sale, promise in zip(sales, promises):
        if sale.promise_text:
            sale.promise = promise
    state = store.load()
    # Rows without an id get one now, so every row can see the others in its history.
    taken = set(state["sales"]) | {sale.id for sale in sales if sale.id}
    for sale in sales:
        while not sale.id:
            candidate = f"V-{secrets.token_hex(2).upper()}"
            if candidate not in taken:
                sale.id = candidate
                taken.add(candidate)
    batch_ids = {sale.id for sale in sales}
    existing_history = [
        Sale.model_validate(item) for key, item in state["sales"].items() if key not in batch_ids
    ]
    # ponytail: O(n²) histories fit the unpaginated demo; index them if batch size grows.
    verdicts = [
        await run_in_threadpool(
            evaluate_and_store,
            sale,
            existing_history + [other for other in sales if other is not sale],
        )
        for sale in sales
    ]
    state = store.load()
    rows = [{"verdict": verdict, "sale": Sale.model_validate(state["sales"][verdict.sale_id]),
             "main_rule": main_evidence(verdict)} for verdict in verdicts]
    rows.sort(key=lambda item: item["verdict"].recoverable_per_minute, reverse=True)
    confusion = confusion_matrix(rows) if any(row["sale"].label or row["sale"].extra.get("veredicto_esperado") for row in rows) else None

    def summarize():
        return {"text": llm.summarize_batch(rows), **llm.describe()}

    reading = await run_in_threadpool(summarize)
    return render_batch(request, results=rows, report=report, confusion=confusion, reading=reading)


try:
    from confirm.router import router as confirm_router
except ImportError:
    confirm_router = APIRouter()
app.include_router(confirm_router)
