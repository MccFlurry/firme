"""Try configured field corrections, re-evaluating the whole sale each time."""

from contracts.types import Counterfactual, Sale, Verdict
from engine.rules import SEVERITIES


def calculate(sale: Sale, verdict: Verdict, facts: dict, rules: list[dict], evaluate_sale) -> Counterfactual | None:
    if verdict.decision == "APROBAR":
        return None
    by_id = {rule["id"]: rule for rule in rules}
    candidate = sale.model_copy(deep=True)
    changes, attempted = [], set()
    while verdict.decision != "APROBAR":
        for evidence in sorted(verdict.evidence, key=lambda item: SEVERITIES.index(item.severity), reverse=True):
            fix = by_id[evidence.rule_id].get("fix")
            if not fix:
                continue
            field, value = fix["field"], fix["value"]
            value = facts.get(value, value) if isinstance(value, str) else value
            attempt = (evidence.rule_id, repr(value))
            if attempt in attempted or getattr(candidate, field) == value:
                continue
            attempted.add(attempt)
            changes.append({"field": field, "from": getattr(candidate, field), "to": value, "reason": fix["reason"]})
            candidate = Sale.model_validate(candidate.model_dump() | {field: value})
            verdict, facts = evaluate_sale(candidate)
            break
        else:
            break
    if verdict.decision == "APROBAR":
        details = "; ".join(f"{change['reason']} ({change['to']})" for change in changes)
        text = f"Si se aplican estos ajustes, esta venta pasaría: {details}."
    else:
        text = "Con los ajustes disponibles, ningún cambio de un solo campo la haría pasar; requiere confirmación del cliente."
    return Counterfactual(changes=changes, resulting_decision=verdict.decision,
                          resulting_cost=verdict.expected_cost, text=text)
