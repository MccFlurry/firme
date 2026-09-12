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


def decide(facts: dict, evidence: list[Evidence], expected_cost: float, costs: dict,
           rules: list[dict] = ()) -> tuple[Decision, str | None]:
    if any(item.severity == "bloqueante" for item in evidence):
        return "RETENER", None
    abstentions = {rule["id"] for rule in rules if rule.get("abstain")}
    for item in evidence:
        if item.rule_id in abstentions:
            return "ABSTENERSE", item.message
    if facts["plan"] is None or facts["price"] is None:
        return "ABSTENERSE", "Falta plan o precio; no se puede contrastar la oferta registrada."
    if expected_cost >= costs["thresholds"]["retain_multiple"] * costs["review"]["cost"]:
        return "RETENER", None
    if expected_cost >= costs["review"]["cost"]:
        return "REVISAR", None
    return "APROBAR", None


def make_alert(sale: Sale, ctx: Context, decision: Decision, evidence: list[Evidence], settings: dict) -> Alert | None:
    if decision not in {"REVISAR", "RETENER", "ABSTENERSE"}:
        return None
    installation = parse_datetime(sale.install_date, settings)
    if installation is None:
        installation = (parse_datetime(sale.registered_at, settings) or current_time(ctx, settings)) + timedelta(
            days=settings["install_ceiling_days"])
    deadline = (installation - timedelta(hours=settings["alert_buffer_hours"])).isoformat()
    if decision == "RETENER":
        return Alert(recipient="Despacho e instalaciones + Supervisor de ventas", urgency="alta", deadline=deadline,
                     action="No despachar. Verificar con el cliente por el enlace de confirmación.")
    if decision == "ABSTENERSE":
        return Alert(recipient="Calidad de venta", urgency="media", deadline=deadline,
                     action="Completar la evidencia o identificar el catálogo de referencia antes de calificar la venta.")
    strongest = max(evidence, key=lambda item: SEVERITIES.index(item.severity), default=None)
    field = f"los datos de «{strongest.rule_name}»" if strongest else "los datos acordados"
    return Alert(recipient="Calidad de venta", urgency="media", deadline=deadline,
                 action=f"Llamar al cliente y validar {field} antes del plazo.")
