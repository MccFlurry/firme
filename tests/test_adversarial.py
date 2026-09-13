"""The team's unchanged adversarial bank is the acceptance contract (T10)."""

import json
import re
from pathlib import Path

import pytest

from app.main import main_evidence
from contracts.types import Context
from engine import evaluate
from engine.ingest import parse

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "data/casos-adversarios.json").read_text())
PRINCIPAL = {
    **{key: None for key in ("BUE-01", "BUE-02", "BUE-03", "BUE-04", "LIM-02")},
    "BUE-05": "R27", "DEF-01": "R03", "DEF-02": "R04", "DEF-03": "R30",
    "DEF-04": "R31", "DEF-05": "R25", "DEF-06": "R14", "DEF-07": "R32",
    "DEF-08": "R23", "AMB-01": "R26", "AMB-02": "R24", "AMB-03": "R37",
    "AMB-04": "R33", "AMB-05": "R38", "AMB-06": "R34", "LIM-01": "R35",
    "LIM-03": "R27", "LIM-04": "R39", "LIM-05": "R36",
}
DECISIONS = {"pasa": {"APROBAR"}, "revisar": {"REVISAR", "RETENER"}, "abstención": {"ABSTENERSE"}}


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_adversarial_bank(case, monkeypatch):
    monkeypatch.setenv("LLM_DISABLE", "1")
    sales, report = parse(CASES)
    assert not report.errors and len(sales) == 24
    sale = next(sale for sale in sales if sale.id == case["id"])
    verdict = evaluate(sale, Context(history=sales))
    assert verdict.decision in DECISIONS[case["veredicto_esperado"]]
    principal = main_evidence(verdict)
    assert (principal.rule_id[:3] if principal else None) == PRINCIPAL[sale.id]


def test_bank_preserves_every_document_input():
    document = (ROOT / "docs/CASOS-ADVERSARIOS.md").read_text()
    inputs = re.findall(r"```json\n(.*?)\n```", document, re.S)
    assert len(inputs) == len(CASES) == len(PRINCIPAL) == 24
    metadata = {"id", "familia", "comparador", "veredicto_esperado", "extra", "customer_name"}  # customer_name: synthetic display name, not part of the bank
    for case, source in zip(CASES, inputs):
        actual = {key: value for key, value in case.items() if key not in metadata}
        if case["id"] == "LIM-04":
            assert actual.pop("fecha_hora_registro") == "2026-08-30T10:00:00-05:00"
            assert "Ancla temporal" in case["extra"]["nota_demo"]
        assert actual == json.loads(source)


def test_contract_columns_csv_and_labels():
    import csv
    import io
    from engine.ingest import CONTRACT_FIELDS

    row = {
        "promesa_declarada": "Plan 200 a 99 soles, instalación en 6 cuotas de 20 soles",
        "velocidad_contratada": 200, "precio_mensual": 99, "cliente_documento": "SIM-30",
        "telefono_1": "900000030", "telefono_2": "900000031", "correo_electronico": "test@example.invalid",
        "direccion": "Av. Simulada, Chiclayo", "nombre_asesor": "ASESOR-014", "equipo": "EQUIPO-CHICLAYO-02",
        "canal": "web", "fecha_hora_registro": "2026-09-01T10:00:00-05:00",
        "ediciones_registro": [{"field": "precio_mensual", "at": "2026-09-01T11:00:00-05:00", "old": "98", "new": "99"}],
        "plazo_estimado_instalacion": 30, "confirmacion_titular": "confirmada",
        "confirmacion_titular_ts": "2026-09-02T10:00:00-05:00", "plazo_vigencia": "Forzoso_6_meses",
        "forma_entrega_recibo": "Electronico", "forma_pago": "Mes_Vencido", "forma_pago_instalacion": "Primer recibo",
        "cargo_instalacion_costo": 120, "cargo_instalacion_cuotas": 6, "tenencia": "Propietario",
        "etapa": "A", "nombre_condominio": "Condominio", "torre": "1", "departamento": "101",
        "score_crediticio": 250, "catalogo_referencia_id": "cartilla", "acta_instalacion_ts": None,
    }
    assert len(row) == len(CONTRACT_FIELDS) == 30
    sales, report = parse([row])
    assert not report.unrecognized and not report.errors
    assert report.mapped == CONTRACT_FIELDS
    assert sales[0].plan == "fibra_200" and sales[0].edits[0].field == "price"
    for key, field in CONTRACT_FIELDS.items():
        if field.startswith("extra."):
            assert sales[0].extra[key] == row[key]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=row)
    writer.writeheader()
    writer.writerow({key: json.dumps(value) if isinstance(value, list) else value for key, value in row.items()})
    csv_sales, report = parse(output.getvalue(), "contract.csv")
    assert not report.errors and csv_sales == sales
    aliases, _ = parse([{"VelocidadContratada": 450, "Precio mensual": 139, "Teléfono 2": "900000030",
                         "Confirmación titular": "enviada", "etiqueta": label} for label in ("pasa", "revisar", "abstencion")])
    assert [sale.label for sale in aliases] == ["buena", "mala", None]
    assert aliases[0].plan == "450 Mbps" and aliases[0].extra["telefono_2"] == "900000030"
    assert aliases[2].extra["veredicto_esperado"] == "abstención"


def test_confirmation_states_precedence_and_window():
    from contracts.types import Confirmation
    from engine.facts import build_facts
    from engine.rules import load_config

    for canonical, status in {"no_enviada": None, "enviada": "pendiente", "no_respondida": "silencio",
                              "confirmada": "confirmada", "confirmada_con_correccion": "corregida", "negada": "desconocida"}.items():
        sales, _ = parse([{"velocidad_contratada": 200, "precio_mensual": 99, "confirmacion_titular": canonical}])
        assert build_facts(sales[0], Context(), load_config("catalog"))["confirmation_status"] == status
    sale = next(sale for sale in parse(CASES)[0] if sale.id == "LIM-04")
    for timestamp, late in (("2026-09-09T10:00:00-05:00", False), ("2026-09-09T10:00:01-05:00", True)):
        sale.extra["confirmacion_titular_ts"] = timestamp
        assert ("R39" in {item.rule_id[:3] for item in evaluate(sale, Context()).evidence}) is late
    confirmation = Confirmation(sale_id=sale.id, token="test", status="desconocida",
                                created_at="2026-08-30T10:00:00-05:00", expires_at="2026-09-09T10:00:00-05:00")
    sale.extra.update(velocidad_contratada=850, catalogo_referencia_id=None)
    verdict = evaluate(sale, Context(confirmation=confirmation))
    assert verdict.decision == "RETENER" and main_evidence(verdict).rule_id == "R25_cliente_desconoce"


def test_cohorts_costs_and_abstention_are_not_defect_estimates():
    from engine.facts import build_facts
    from engine.rules import load_config

    costs, catalog = load_config("costs"), load_config("catalog")
    expected = {"instalacion_fallida": (80, "P-09", .05, "P-08"), "baja_temprana": (95, "P-11", .06, "P-10"),
                "reclamo": (45, "P-13", .10, "P-12"), "reversion_facturacion": (58, "P-15", .15, "P-14")}
    for name, (amount, id, probability, pid) in expected.items():
        item = costs["outcomes"][name]
        assert (item["cost"], item["id"], item["base_probability"]["value"], item["base_probability"]["id"]) == (amount, id, probability, pid)
    assert sum(item["cost"] * item["base_probability"]["value"] for item in costs["outcomes"].values()) == pytest.approx(22.9)
    assert costs["review"]["cost"] == costs["review"]["minutes"] * costs["review"]["cost_per_minute"] == 30
    assert costs["recoverability"] == 1 and costs["thresholds"]["retain_multiple"] == 4
    for rule in load_config("rules"):
        if rule["severity"] in {"media", "alta", "bloqueante"}:
            assert all(value >= expected[outcome][2] for outcome, value in rule["impacts"].items())
        if int(rule["id"][1:3]) >= 30:
            assert "§" in rule["source"] and rule["source"] == rule["fuente"]
    sales, _ = parse(CASES)
    sale = next(sale for sale in sales if sale.id == "BUE-05")
    assert build_facts(sale, Context(), catalog)["prior"] == .10
    for channel in costs["priors"]:
        sale.channel = channel
        assert evaluate(sale, Context()).decision == "APROBAR"
    ambiguous = evaluate(next(sale for sale in sales if sale.id == "AMB-03"), Context())
    assert ambiguous.expected_cost == 0 and ambiguous.outcome_probs == ambiguous.outcome_costs == {}
    assert ambiguous.alert.recipient == "Calidad de venta" and ambiguous.recoverable_per_minute == 2.5
    confirmed_defect = evaluate(next(sale for sale in sales if sale.id == "DEF-04"), Context())
    assert confirmed_defect.evidence[0].values["expected_monthly_total"] == 109
    assert "confirmación ya existe" in confirmed_defect.counterfactual.text


def test_condominium_unit_and_known_web_surface():
    sales, _ = parse(CASES)
    condominium = next(sale for sale in sales if sale.id == "AMB-06")
    condominium.extra.update(torre="A", departamento="101")
    condominium.registered_at = "2026-09-12T12:00:00-05:00"
    neighbor = condominium.model_copy(deep=True, update={"id": "NEIGHBOR"})
    neighbor.extra["departamento"] = "102"
    assert evaluate(condominium, Context(history=[neighbor])).decision == "APROBAR"
    web = next(sale for sale in sales if sale.id == "AMB-03")
    web.extra["catalogo_referencia_id"] = "web_hogar"
    web.price = 59.5
    web.promise_text = "850 megas a 59.50 soles"
    assert evaluate(web, Context()).decision == "APROBAR"
