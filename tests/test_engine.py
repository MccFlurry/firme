from datetime import datetime
from types import SimpleNamespace

import pytest

from contracts.types import Confirmation, Context, FieldEdit, Promise, Sale
from engine import evaluate
from engine.facts import build_facts
from engine.llm import explain_for_client, normalize_promise
from engine.rules import load_config


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def sale(**changes):
    values = dict(
        id="V-TEST", seller_id="S-DEMO", channel="web", customer_name="Cliente Demo",
        customer_doc="00000001", phone="900000001", email="demo@example.invalid",
        address="Av. Perú 123", district="chiclayo_centro", plan="fibra_200",
        price=99.0, registered_at="2026-09-12T10:00:00-05:00",
        install_date="2026-09-13T10:00:00-05:00", fill_seconds=120,
        consent_evidence="firma",
    )
    return Sale(**(values | changes))


def context(status=None, **changes):
    confirmation = Confirmation(
        sale_id="V-TEST", token="demo", status=status, note="El precio acordado era otro.",
        created_at="2026-09-12T10:00:00-05:00", expires_at="2026-09-13T10:00:00-05:00",
    ) if status else None
    return Context(now="2026-09-12T10:00:00-05:00", confirmation=confirmation, **changes)


def ids(verdict):
    return {item.rule_id for item in verdict.evidence}


def test_clean_sale_approved():
    verdict = evaluate(sale(), context())
    assert verdict.decision == "APROBAR"
    assert verdict.expected_cost == pytest.approx(0.04 * 0.25 * 45 + 0.04 * 0.15 * 95)
    assert verdict.evidence == []
    assert verdict.alert is None
    assert verdict.llm_mode == "determinista"


def test_low_price_evidence_and_counterfactual():
    original = sale(price=50)
    verdict = evaluate(original, context())
    assert verdict.decision == "REVISAR"
    evidence = next(e for e in verdict.evidence if e.rule_id == "R03_precio_bajo_tarifa")
    assert evidence.values["price"] == 50
    assert evidence.values["catalog_price"] == 99.0
    assert evidence.origin == "PUBLICO"
    assert evidence.condition and evidence.source
    assert verdict.counterfactual.resulting_decision == "APROBAR"
    assert verdict.counterfactual.changes == [
        {"field": "price", "from": 50.0, "to": 99.0, "reason": "igualar al tarifario vigente"}
    ]
    assert evaluate(original.model_copy(update={"price": 99.0}), context()).decision == "APROBAR"
    assert original.price == 50
    assert verdict.alert.recipient == "Calidad de venta"
    assert datetime.fromisoformat(verdict.alert.deadline) == datetime.fromisoformat("2026-09-12T10:00:00-05:00")
    assert verdict.recoverable_per_minute == pytest.approx(verdict.expected_cost / 12)


def test_unsupported_promise_claim():
    verdict = evaluate(sale(promise_text="Fibra 200 a S/ 99.00, gratis para siempre"), context())
    evidence = next(e for e in verdict.evidence if e.rule_id == "R23_promesa_insostenible")
    assert evidence.strength == "linguistica"
    assert evidence.values["unsupported_claims"] == ["gratis para siempre"]
    assert verdict.promise.claims == ["gratis para siempre"]


@pytest.mark.parametrize("status,rule", [
    ("desconocida", "R25_cliente_desconoce"), ("silencio", "R26_sin_respuesta"),
    ("corregida", "R24_cliente_corrige"),
])
def test_confirmation_signals(status, rule):
    verdict = evaluate(sale(), context(status))
    assert rule in ids(verdict)
    if status == "desconocida":
        assert verdict.decision == "RETENER"
        assert verdict.alert.urgency == "alta"
        assert "requiere confirmación del cliente" in verdict.counterfactual.text
    elif status == "silencio":
        assert verdict.decision == "REVISAR"
        assert verdict.alert.recipient == "Calidad de venta"
    else:
        assert "El precio acordado era otro." in verdict.evidence[0].message


def test_confirmed_clears_identity_and_promise_record_only():
    original = sale(consent_evidence=None, promise=Promise(price=99.0), price=50)
    pending = evaluate(original, context())
    confirmed = evaluate(original, context("confirmada"))
    assert any(e.edge == "identidad" for e in pending.evidence)
    assert any(e.edge == "promesa-registro" for e in pending.evidence)
    assert not any(e.edge in {"identidad", "promesa-registro"} for e in confirmed.evidence)
    assert "R03_precio_bajo_tarifa" in ids(confirmed)
    assert confirmed.expected_cost < pending.expected_cost


def test_burst_counts_current_once_and_excludes_future_and_old():
    current = sale()
    history = [current, sale(id="V-2", registered_at="2026-09-12T09:55:00-05:00"),
               sale(id="V-3", registered_at="2026-09-12T09:52:00-05:00"),
               sale(id="V-4", registered_at="2026-09-12T09:49:00-05:00"),
               sale(id="V-5", registered_at="2026-09-12T10:01:00-05:00")]
    verdict = evaluate(current, context(history=history))
    evidence = next(e for e in verdict.evidence if e.rule_id == "R18_rafaga")
    assert evidence.values["burst_count"] == 3


def test_phone_collision_and_normalized_address():
    other = sale(id="V-2", customer_name="Otra Persona Demo", phone="900 000 001", address="AV PERU, 123")
    verdict = evaluate(sale(), context(history=[other]))
    assert "R14_colision_telefono" in ids(verdict)
    assert "R17_direccion_repetida" in ids(verdict)
    cleared = evaluate(sale(), context("confirmada", history=[other]))
    assert "R14_colision_telefono" not in ids(cleared)


@pytest.mark.parametrize("changes,missing", [
    ({"plan": None, "price": None}, {"plan", "price"}),
    ({"plan": None}, {"plan"}),
    ({"price": None}, {"price"}),
])
def test_abstention(changes, missing):
    verdict = evaluate(sale(**changes), context())
    assert verdict.decision == "ABSTENERSE"
    assert verdict.abstain_reason
    assert missing <= set(verdict.missing_fields)
    assert verdict.alert.recipient == "Calidad de venta"


def test_deterministic_normalization():
    promise, mode = normalize_promise(
        "Plan 200, 200 megas a S/ 99,00, primer mes gratis, sin contrato; instalación en 2 días",
        load_config("catalog"),
    )
    assert mode == "determinista"
    assert promise.source == "deterministic"
    assert (promise.plan, promise.speed_mbps, promise.price) == ("fibra_200", 200, 99.0)
    assert promise.promo == "primer_mes_gratis"
    assert promise.install_days == 2
    assert promise.claims == ["sin contrato"]


def test_all_missing_or_invalid_dates_degrade_without_crashing():
    verdict = evaluate(Sale(id="V-empty"), Context(now="invalid"))
    assert verdict.decision == "ABSTENERSE"
    facts = build_facts(sale(registered_at="bad", install_date="bad", fill_seconds=None), context(), load_config("catalog"))
    assert facts["install_within_window"] is None
    assert facts["hour"] is None
    assert facts["fill_seconds"] is None
    invalid = evaluate(sale(install_date="bad", registered_at="bad"), context())
    assert {"install_date", "registered_at"} <= set(invalid.missing_fields)


@pytest.mark.parametrize("changes,rule", [
    ({"plan": "inexistente"}, "R04_plan_inexistente"),
    ({"promo": "primer_mes_gratis"}, "R05_promo_no_aplicable"),
    ({"district": "pimentel"}, "R10_sin_cobertura"),
    ({"install_date": "2026-10-15T10:00:00-05:00"}, "R11_instalacion_fuera_ventana"),
    ({"extra": {"billing_amount": 200}}, "R12_facturacion_distinta"),
    ({"fill_seconds": 20}, "R19_llenado_rapido"),
    ({"registered_at": "2026-09-12T02:40:00-05:00"}, "R20_hora_atipica"),
    ({"channel": "campo"}, "R27_prior_canal"),
])
def test_other_comparators_and_signals(changes, rule):
    assert rule in ids(evaluate(sale(**changes), context()))


def test_edit_signals_only_after_submission():
    edits = [FieldEdit(field=field, at="2026-09-12T10:05:00-05:00")
             for field in ("price", "price", "customer_name")]
    verdict = evaluate(sale(edits=edits), context())
    assert {"R21_reedicion_precio", "R22_reedicion_identidad"} <= ids(verdict)
    old = [FieldEdit(field="customer_doc", at="2026-09-12T09:00:00-05:00")]
    assert "R22_reedicion_identidad" not in ids(evaluate(sale(edits=old), context()))


def test_llm_success_and_timeout_fallback(monkeypatch):
    from engine import llm

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    calls = []

    class Client:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] == 10
            assert kwargs["max_retries"] == 0
            self.messages = self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(
                type="text", text='{"promises":[{"plan":"fibra_200","price":99.0}]}')])

    monkeypatch.setattr(llm.anthropic, "Anthropic", Client)
    promise, mode = normalize_promise("200 megas S/ 99.00", load_config("catalog"))
    assert mode == "llm" and promise.source == "llm"
    assert calls[0]["model"] == "claude-opus-5"
    assert calls[0]["output_config"] == {"effort": "low"}
    assert calls[0]["max_tokens"] == 8192

    def fail(self, **kwargs):
        raise TimeoutError("offline")

    monkeypatch.setattr(Client, "create", fail)
    promise, mode = normalize_promise("200 megas S/ 99.00", load_config("catalog"))
    assert mode == "determinista" and promise.price == 99.0
    text, mode = explain_for_client(sale(), promise)
    assert mode == "determinista" and "99.00" in text and "Cliente Demo" in text


def test_noisy_or_and_prior_counted_once():
    verdict = evaluate(sale(price=50), context())
    assert verdict.outcome_probs["reclamo"] == pytest.approx(1 - (1 - 0.04 * 0.25) * (1 - 0.35))
    assert verdict.outcome_probs["reversion_facturacion"] == pytest.approx(0.4)
    assert verdict.outcome_costs["reclamo"] == pytest.approx(verdict.outcome_probs["reclamo"] * 45)
    assert verdict.expected_cost == pytest.approx(sum(verdict.outcome_costs.values()))
    cohort = evaluate(sale(channel="campo"), context())
    assert cohort.expected_cost == pytest.approx(0.12 * 0.25 * 45 + 0.12 * 0.15 * 95)
    assert cohort.decision == "APROBAR"  # the prior alone never sends a clean sale to review
    assert ids(cohort) == {"R27_prior_canal"}


@pytest.mark.parametrize("amount,decision", [(29.99, "APROBAR"), (30, "REVISAR"), (119.99, "REVISAR"), (120, "RETENER")])
def test_economic_thresholds(amount, decision):
    from engine.cost import decide

    facts = build_facts(sale(), context(), load_config("catalog"))
    assert decide(facts, [], amount, load_config("costs")) == (decision, None)
    blocking = evaluate(sale(), context("desconocida")).evidence
    assert decide(facts, blocking, 0, load_config("costs")) == ("RETENER", None)


def test_counterfactual_accumulates_fixes_and_does_not_mutate():
    original = sale(price=50, install_date="2026-10-15T10:00:00-05:00")
    before = original.model_dump()
    verdict = evaluate(original, context())
    assert [change["field"] for change in verdict.counterfactual.changes] == ["price", "install_date"]
    assert verdict.counterfactual.resulting_decision == "APROBAR"
    fixed = original.model_copy(update={change["field"]: change["to"] for change in verdict.counterfactual.changes})
    assert evaluate(fixed, context()).expected_cost == pytest.approx(verdict.counterfactual.resulting_cost)
    assert original.model_dump() == before


def test_counterfactual_conflicting_fixes_terminate_without_approval():
    verdict = evaluate(sale(price=50, promise=Promise(price=50)), context())
    assert verdict.counterfactual.resulting_decision != "APROBAR"
    assert len(verdict.counterfactual.changes) == 2
    assert "requiere confirmación" in verdict.counterfactual.text


@pytest.mark.parametrize("hours,triggered", [(720, False), (721, True), (-1, True)])
def test_install_window_boundary(hours, triggered):
    from datetime import timedelta

    installation = datetime.fromisoformat(sale().registered_at) + timedelta(hours=hours)
    verdict = evaluate(sale(install_date=installation.isoformat()), context())
    assert ("R11_instalacion_fuera_ventana" in ids(verdict)) is triggered


def test_alert_without_install_date_and_unrelated_confirmation():
    verdict = evaluate(sale(price=50, install_date=None), context())
    assert verdict.alert.deadline == "2026-10-11T10:00:00-05:00"
    ctx = context("confirmada")
    ctx.confirmation.sale_id = "V-unrelated"
    assert "R13_sin_consentimiento" in ids(evaluate(sale(consent_evidence=None), ctx))


def test_catalog_aliases_and_applicable_promo():
    verdict = evaluate(sale(plan="200 megas", promo="descuento 3m", price=79.0), context())
    assert verdict.decision == "APROBAR"
    assert "R03_precio_bajo_tarifa" not in ids(verdict)
    assert "R05_promo_no_aplicable" not in ids(verdict)


@pytest.mark.parametrize("promise,rule", [
    (Promise(plan="plan_imposible"), "R01_plan_prometido_inexistente"),
    (Promise(plan="fibra_200", price=30), "R02_precio_prometido_distinto"),
    (Promise(plan="fibra_300"), "R06_plan_promesa_registro"),
    (Promise(promo="descuento_3m"), "R08_promo_promesa_registro"),
    (Promise(install_days=2), "R09_fecha_promesa_registro"),
    (Promise(speed_mbps=9000), "R28_velocidad_prometida"),
    (Promise(plan="fibra_200", promo="primer_mes_gratis"), "R29_promo_prometida_no_aplicable"),
])
def test_promise_comparators(promise, rule):
    assert rule in ids(evaluate(sale(promise=promise), context()))


def test_catalog_and_rules_have_traceable_origins():
    rules = load_config("rules")
    required = {"id", "name", "description", "condition", "severity", "message", "source", "origen", "fuente",
                "edge", "strength", "inputs", "impacts", "fix"}
    assert len(rules) >= 14 and len({rule["id"] for rule in rules}) == len(rules)
    assert {rule["edge"] for rule in rules} == {
        "promesa-catalogo", "promesa-registro", "catalogo-registro", "registro-entrega", "identidad", "senal",
    }
    for rule in rules:
        assert required <= rule.keys()
        assert rule["origen"] in {"SUPUESTO_DEMO", "PUBLICO"} and rule["fuente"]
        assert all(0 <= probability <= 1 for probability in rule["impacts"].values())
    for name in ("catalog", "costs", "settings", "lexicon"):
        config = load_config(name)
        assert config["origen"] == "SUPUESTO_DEMO" and config["fuente"]


def test_llm_empty_result_and_api_error_degrade(monkeypatch):
    from engine import llm

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    class Client:
        def __init__(self, **kwargs):
            self.messages = self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def create(self, **kwargs):
            return SimpleNamespace(content=[SimpleNamespace(type="text", text='{"text":"Texto de prueba"}')])

    monkeypatch.setattr(llm.anthropic, "Anthropic", Client)
    promise, mode = normalize_promise("Plan 200 S/ 99.00", load_config("catalog"))
    assert mode == "determinista" and promise.plan == "fibra_200"
    assert explain_for_client(sale(), promise) == ("Texto de prueba", "llm")

    def fail(self, **kwargs):
        raise RuntimeError("API unavailable")

    monkeypatch.setattr(Client, "create", fail)
    assert explain_for_client(sale(), promise)[1] == "determinista"
