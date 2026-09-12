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
    }


def test_batch_without_id_column_still_detects_collisions(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "STATE_PATH", tmp_path / "state.json")
    payload = (
        '[{"cliente": "Ana Quispe", "telefono": "912345678", "plan": "fibra_500", "precio": 99.00, "dni": "11111111"},'
        ' {"cliente": "Luis Paredes", "telefono": "912345678", "plan": "fibra_500", "precio": 99.00, "dni": "22222222"}]'
    )
    response = TestClient(app).post("/lote", data={"payload": payload})
    assert response.status_code == 200
    state = store.load()
    assert len(state["sales"]) == 2
    fired = [
        {item["rule_id"] for item in verdict["evidence"]} for verdict in state["verdicts"].values()
    ]
    assert all("R14_colision_telefono" in rules for rules in fired)
