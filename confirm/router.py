"""Customer confirmation screens: /confirm/* and the client link /c/{token}."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from app import store
from confirm import service
from contracts.types import Promise, Sale
from engine.llm import explain_for_client

CONFIRM_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(CONFIRM_DIR / "templates"))
router = APIRouter()

DONE_MESSAGES = {
    "confirmada": "Tu confirmación quedó registrada. Gracias por ayudarnos a que lo prometido sea lo entregado.",
    "corregida": "Registramos tu corrección. Nuestro equipo revisará la oferta y te contactará.",
    "desconocida": "Registramos que no reconoces este servicio. Revisaremos qué ocurrió y te contactaremos.",
}


def _client_context(request: Request, sale_id: str, confirmation):
    state = store.load()
    sale = Sale.model_validate(state["sales"][sale_id])
    verdict = state["verdicts"].get(sale_id, {})
    promise = sale.promise
    if promise is None and verdict.get("promise"):
        promise = Promise.model_validate(verdict["promise"])
    if promise is None:
        promise = Promise(raw_text=sale.promise_text or "")
    text, mode = explain_for_client(sale, promise)
    return {
        "request": request,
        "sale": sale,
        "confirmation": confirmation,
        "text": text,
        "mode": mode,
    }


@router.post("/confirm/create/{sale_id}")
def create_confirmation(sale_id: str):
    try:
        service.create(sale_id)
    except KeyError:
        raise HTTPException(404, "No encontramos esta venta.")
    return RedirectResponse(f"/ventas/{sale_id}", status_code=303)


@router.get("/c/{token}")
def client_screen(request: Request, token: str):
    sale_id, confirmation = service.find_by_token(token)
    if confirmation is None:
        raise HTTPException(404, "Este enlace de confirmación no existe o ya no es válido.")
    context = _client_context(request, sale_id, confirmation)
    return templates.TemplateResponse(request=request, name="client.html", context=context)


@router.post("/c/{token}")
async def respond(request: Request, token: str):
    sale_id, confirmation = service.find_by_token(token)
    if confirmation is None:
        raise HTTPException(404, "Este enlace de confirmación no existe o ya no es válido.")
    form = await request.form(max_fields=10)
    status = (form.get("status") or "").strip()
    if status not in {"confirmada", "corregida", "desconocida"}:
        raise HTTPException(400, "Elige una de las opciones para continuar.")
    note = (form.get("note") or "").strip() or None
    confirmation = await run_in_threadpool(service.respond, token, status, note)
    return templates.TemplateResponse(request=request, name="done.html", context={
        "request": request,
        "confirmation": confirmation,
        "message": DONE_MESSAGES.get(status, "Gracias, tu respuesta quedó registrada."),
    })


@router.post("/confirm/expire/{sale_id}")
async def expire(sale_id: str):
    try:
        await run_in_threadpool(service.expire, sale_id)
    except KeyError:
        raise HTTPException(404, "No encontramos esta venta.")
    return RedirectResponse(f"/ventas/{sale_id}", status_code=303)
