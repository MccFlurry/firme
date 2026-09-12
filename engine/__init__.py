"""Public sale evaluation entrypoint; input contracts are never mutated."""

from contracts.types import Context, Sale, Verdict
from engine.cost import calculate_cost, decide, make_alert
from engine.counterfactual import calculate as counterfactual
from engine.facts import build_facts, current_time, parse_datetime
from engine.llm import normalize_promise
from engine.rules import SEVERITIES, STRENGTHS, evaluate_rules, load_config


def evaluate(sale: Sale, ctx: Context) -> Verdict:
    catalog, rules, costs, settings = (load_config(name) for name in ("catalog", "rules", "costs", "settings"))
    ctx = ctx.model_copy(update={"now": current_time(ctx, settings).isoformat()})
    llm_mode = "llm" if sale.promise and sale.promise.source == "llm" else "determinista"
    if sale.promise is None and sale.promise_text:
        promise, llm_mode = normalize_promise(sale.promise_text, catalog)
        sale = sale.model_copy(update={"promise": promise})

    def evaluate_sale(candidate):
        facts = build_facts(candidate, ctx, catalog, settings, costs)
        evidence = evaluate_rules(facts, rules)
        probabilities, amounts, expected_cost = calculate_cost(evidence, facts["prior"], costs)
        decision, abstain_reason = decide(facts, evidence, expected_cost, costs)
        missing = [field for field in (
            "seller_id", "channel", "customer_name", "customer_doc", "phone", "email", "address",
            "district", "plan", "price", "install_date", "registered_at", "fill_seconds", "consent_evidence",
        ) if facts[field] is None]
        if candidate.promise is None:
            missing.append("promise")
        if facts["billing_amount"] is None:
            missing.append("extra.billing_amount")
        for field in ("registered_at", "install_date"):
            if parse_datetime(getattr(candidate, field), settings) is None and field not in missing:
                missing.append(field)
        verdict = Verdict(
            sale_id=candidate.id, decision=decision, expected_cost=expected_cost,
            review_cost=costs["review"]["cost"], outcome_probs=probabilities, outcome_costs=amounts,
            severity=max((item.severity for item in evidence), key=SEVERITIES.index, default=None),
            strength=max((item.strength for item in evidence), key=STRENGTHS.index, default=None),
            evidence=evidence, counterfactual=None, missing_fields=missing, abstain_reason=abstain_reason,
            llm_mode=llm_mode, recoverable_per_minute=expected_cost * costs["recoverability"] / costs["review"]["minutes"],
            alert=make_alert(candidate, ctx, decision, evidence, settings),
            config_origins={rule["id"]: rule["origen"] for rule in rules}, promise=candidate.promise,
        )
        return verdict, facts

    verdict, facts = evaluate_sale(sale)
    verdict.counterfactual = counterfactual(sale, verdict, facts, rules, evaluate_sale)
    return verdict
