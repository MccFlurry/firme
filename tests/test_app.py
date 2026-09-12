from fastapi.testclient import TestClient

from app import store
from app.main import app, confusion_matrix
from contracts.types import Sale, Verdict


def test_demo_batch_uses_every_row_as_history(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "STATE_PATH", tmp_path / "state.json")

    response = TestClient(app).post("/lote", data={"demo": "1"})

    assert response.status_code == 200
    state = store.load()
    rows = [
        {"sale": Sale.model_validate(sale), "verdict": Verdict.model_validate(state["verdicts"][sale_id])}
        for sale_id, sale in state["sales"].items()
    ]
    matrix = confusion_matrix(rows)
    assert matrix == {
        "tp": 13,
        "fp": 0,
        "tn": 12,
        "fn": 0,
        "precision": 1.0,
        "recall": 1.0,
        "labelled": 25,
        "abstained": 0,
        "expected_abstentions": 0,
        "correct_abstentions": 0,
    }


def test_batch_without_id_column_still_detects_collisions(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "STATE_PATH", tmp_path / "state.json")
    payload = (
        '[{"cliente": "Ana Quispe", "telefono": "912345678", "plan": "fibra_200", "precio": 99.00, "dni": "11111111"},'
        ' {"cliente": "Luis Paredes", "telefono": "912345678", "plan": "fibra_200", "precio": 99.00, "dni": "22222222"}]'
    )
    response = TestClient(app).post("/lote", data={"payload": payload})
    assert response.status_code == 200
    state = store.load()
    assert len(state["sales"]) == 2
    fired = [
        {item["rule_id"] for item in verdict["evidence"]} for verdict in state["verdicts"].values()
    ]
    assert all("R14_colision_telefono" in rules for rules in fired)


def test_adversarial_batch_and_invoice_pair(monkeypatch, tmp_path):
    import json
    from app.main import ADVERSARIAL_PATH

    monkeypatch.setattr(store, "STATE_PATH", tmp_path / "state.json")
    client = TestClient(app)
    assert client.get("/").status_code == 200  # Web tiers with unknown price still render.
    response = client.post("/lote", data={"demo": "adversarios"})
    assert response.status_code == 200 and "3 / 3" in response.text
    state = store.load()
    assert len(state["sales"]) == 24
    rows = [{"sale": Sale.model_validate(sale), "verdict": Verdict.model_validate(state["verdicts"][id])}
            for id, sale in state["sales"].items()]
    matrix = confusion_matrix(rows)
    assert (matrix["tp"], matrix["tn"], matrix["fp"], matrix["fn"], matrix["correct_abstentions"]) == (14, 7, 0, 0, 3)
    for id, rule in (("DEF-04", "R31"), ("LIM-01", "R35"), ("AMB-03", "R37"), ("LIM-05", "R36")):
        response = client.get(f"/ventas/{id}")
        assert response.status_code == 200 and rule in response.text and "PUBLICO" in response.text
        assert "docs/EVIDENCIA-PUBLICA.md §" in response.text and "P-16 × P-17 = S/ 30,00" in response.text
        assert (">Abstenerse<" if id == "AMB-03" else ">Revisar<") in response.text
    assert "AMB-03" in client.get("/bandeja").text
    pair = [case for case in json.loads(ADVERSARIAL_PATH.read_text()) if case["id"] in {"BUE-02", "DEF-04"}]
    response = client.post("/lote", data={"payload": json.dumps(pair)})
    assert response.status_code == 200
    verdicts = store.load()["verdicts"]
    assert verdicts["BUE-02"]["decision"] == "APROBAR" and not verdicts["BUE-02"]["evidence"]
    assert [e["rule_id"] for e in verdicts["DEF-04"]["evidence"]] == ["R31_recibo_fisico_no_declarado"]
