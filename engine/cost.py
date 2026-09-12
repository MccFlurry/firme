"""Noisy-OR costs, economic decisions and timely alerts."""

from datetime import timedelta
from math import prod

from contracts.types import Alert, Context, Decision, Evidence, Sale
from engine.facts import current_time, parse_datetime
from engine.rules import SEVERITIES


def calculate_cost(evidence: list[Evidence], prior: float, costs: dict) -> tuple[dict, dict, float]:
    probabilities = {}
    amounts = {}
    for outcome, item in costs["outcomes"].items():
        contributions = [prior * costs["prior_impacts"].get(outcome, 0)]
        contributions.extend(entry.impacts.get(outcome, 0) for entry in evidence)
        probabilities[outcome] = 1 - prod(1 - probability for probability in contributions)
        amounts[outcome] = probabilities[outcome] * item["cost"]
    return probabilities, amounts, sum(amounts.values())


def decide(facts: dict, evidence: list[Evidence], expected_cost: float, costs: dict) -> tuple[Decision, str | None]:
    if facts["plan"] is None and facts["price"] is None:
        return "ABSTENERSE", "Faltan plan y precio; no se puede contrastar la oferta registrada."
    if not any(facts[field] for field in ("customer_doc", "phone", "email")):
        return "ABSTENERSE", "No hay documento, teléfono ni correo para identificar al cliente."
    if any(item.severity == "bloqueante" for item in evidence):
        return "RETENER", None
    if expected_cost >= costs["thresholds"]["retain_multiple"] * costs["review"]["cost"]:
        return "RETENER", None
    if expected_cost >= costs["review"]["cost"]:
        return "REVISAR", None
    return "APROBAR", None


def make_alert(sale: Sale, ctx: Context, decision: Decision, evidence: list[Evidence], settings: dict) -> Alert | None:
    if decision not in {"REVISAR", "RETENER"}:
        return None
    installation = parse_datetime(sale.install_date, settings)
    if installation is None:
        installation = current_time(ctx, settings) + timedelta(hours=settings["install_window_hours"])
    deadline = (installation - timedelta(hours=settings["alert_buffer_hours"])).isoformat()
    if decision == "RETENER":
        return Alert(recipient="Despacho e instalaciones + Supervisor de ventas", urgency="alta", deadline=deadline,
                     action="No despachar. Verificar con el cliente por el enlace de confirmación.")
    strongest = max(evidence, key=lambda item: SEVERITIES.index(item.severity), default=None)
    field = f"los datos de «{strongest.rule_name}»" if strongest else "los datos acordados"
    return Alert(recipient="Calidad de venta", urgency="media", deadline=deadline,
                 action=f"Llamar al cliente y validar {field} antes del plazo.")
