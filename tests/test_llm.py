import json
from types import SimpleNamespace

import httpx
import pytest

from contracts.types import Context, Sale
from engine import evaluate, llm
from engine.ingest import parse
from engine.rules import load_config


def mock_http(monkeypatch, response):
    calls = []

    def post(self, url, **kwargs):
        calls.append((url, kwargs))
        if isinstance(response, Exception):
            raise response
        return httpx.Response(200, request=httpx.Request("POST", url), json={
            "choices": [{"message": {"content": json.dumps(response)}}],
        })

    monkeypatch.setenv("OPENCODE_API_KEY", "test-key")
    monkeypatch.setattr(llm.httpx.Client, "post", post)
    return calls


def test_batch_extraction_once_session_and_grounded_claims(monkeypatch):
    calls = mock_http(monkeypatch, {"promises": [
        {"plan": "fibra_850", "price": 59.5, "claims": ["el precio nunca sube", "router gratis inventado"]},
        {"price": 99},
    ]})
    texts = ["Fibra 850 a S/ 59.50, velocidad garantizada y el precio nunca sube", "S/ 99"]
    promises = llm.normalize_promises(texts, load_config("catalog"))
    assert len(calls) == 1 and len(promises) == 2
    assert promises[0].source == "llm" and promises[1].price == 99
    assert "router gratis inventado" not in promises[0].claims
    verdict = evaluate(Sale(id="AI", phone="900000009", plan="fibra_850", price=59.5,
                            promise=promises[0], consent_evidence="firma"), Context())
    evidence = next(e for e in verdict.evidence if e.rule_id == "R23_promesa_insostenible")
    assert {"text": "el precio nunca sube", "origen": "IA"} in evidence.values["unsupported_claims"]
    assert "velocidad garantizada" in evidence.values["unsupported_claims"]
    llm.normalize_promises(texts, load_config("catalog"))
    assert calls[0][1]["headers"]["x-opencode-session"] == calls[1][1]["headers"]["x-opencode-session"]
    body = calls[0][1]["json"]
    assert body["model"] == "deepseek-v4-flash" and body["temperature"] == 0
    assert body["response_format"] == {"type": "json_object"}
    assert llm.describe()["provider"] == "OpenCode Go"


@pytest.mark.parametrize("response", [httpx.ReadTimeout("offline"), {"promises": "invalid"},
                                      {"promises": []}, {"promises": [{"price": -2}]}])
def test_bad_provider_response_degrades(monkeypatch, response):
    mock_http(monkeypatch, response)
    promise, mode = llm.normalize_promise("500 megas S/ 99", load_config("catalog"))
    assert mode == "determinista" and promise.price == 99 and promise.source == "deterministic"


def test_anthropic_priority_then_opencode_on_invalid_json(monkeypatch):
    calls = mock_http(monkeypatch, {"promises": [{"price": 59.5}]})
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test")

    class Client:
        def __init__(self, **kwargs):
            assert kwargs == {"timeout": 10, "max_retries": 0}
            self.messages = self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def create(self, **kwargs):
            assert kwargs["model"] == "claude-opus-5"
            return SimpleNamespace(content=[SimpleNamespace(type="text", text='{"promises":[{"price":59.5}]}')])

    monkeypatch.setattr(llm.anthropic, "Anthropic", Client)
    assert llm.normalize_promise("S/ 59.50", load_config("catalog"))[1] == "llm"
    assert calls == [] and llm.describe()["provider"] == "Anthropic"
    monkeypatch.setattr(Client, "create", lambda *a, **k: SimpleNamespace(
        content=[SimpleNamespace(type="text", text="invalid JSON")]))
    assert llm.normalize_promise("S/ 59.50", load_config("catalog"))[1] == "llm"
    assert len(calls) == 1 and llm.describe()["provider"] == "OpenCode Go"


def test_key_file_override_and_disable(monkeypatch):
    calls = mock_http(monkeypatch, {"text": "ok"})
    llm.AUTH_PATH.write_text(json.dumps({"opencode-go": {"key": "local-test"}}))
    monkeypatch.delenv("OPENCODE_API_KEY")
    monkeypatch.setenv("LLM_MODEL", "custom-model")
    assert llm._chat([{"role": "user", "content": "data"}]) == {"text": "ok"}
    assert calls[-1][1]["headers"]["Authorization"] == "Bearer local-test"
    assert calls[-1][1]["json"]["model"] == "custom-model"
    monkeypatch.setenv("OPENCODE_API_KEY", "env-test")
    llm._chat([])
    assert calls[-1][1]["headers"]["Authorization"] == "Bearer env-test"
    monkeypatch.setenv("LLM_DISABLE", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    assert llm._chat([]) is None and len(calls) == 2
    assert llm.describe()["model"] is None


def test_semantic_mapping_is_applied_once_without_overwriting(monkeypatch):
    calls = mock_http(monkeypatch, {"mapping": {
        "Nro. Cel. Titular": "phone", "Tarifa mensual": "price", "ruido": "decision",
        "Reemplazo": "plan", "extra": "promise",
    }})
    sales, report = parse([
        {"Nro. Cel. Titular": "912345678", "Tarifa mensual": 59.5, "plan": "fibra_850",
         "Reemplazo": "fraud", "ruido": "RETENER"},
        {"Nro. Cel. Titular": "923456789", "Tarifa mensual": 99, "plan": "fibra_500"},
    ])
    assert len(calls) == 1 and sales[0].phone == "912345678" and sales[1].price == 99
    assert sales[0].plan == "fibra_850" and sales[0].extra["ruido"] == "RETENER"
    assert report.mapped_by_ai == {"Nro. Cel. Titular": "phone", "Tarifa mensual": "price"}
    assert "ruido" in report.unrecognized and "phone" not in report.missing


def test_batch_call_budget_and_lazy_cached_verdict(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from app import store
    from app.main import app
    from app.services import evaluate_and_store

    monkeypatch.setattr(store, "STATE_PATH", tmp_path / "state.json")
    calls = mock_http(monkeypatch, {
        "mapping": {"Nro. Cel. Titular": "phone", "Tarifa mensual": "price"},
        "promises": [{"price": 59.5}, {"price": 59.5}],
        "text": "El motor determina la revisión con las reglas configuradas.",
    })
    client = TestClient(app)
    rows = [{"id": f"AI-{i}", "Nro. Cel. Titular": f"90000000{i}", "Tarifa mensual": 59.5,
             "plan": "fibra_850", "promesa": "Fibra 850 S/ 59.50", "channel": "web"} for i in range(2)]
    response = client.post("/lote", data={"payload": json.dumps(rows)})
    assert response.status_code == 200 and "mapeado por IA" in response.text
    assert "Lectura del lote" in response.text and len(calls) == 3
    assert not store.load().get("explanations")
    response = client.get("/ventas/AI-0")
    assert "Por qué, en palabras" in response.text and len(calls) == 4
    assert store.load()["explanations"]["AI-0"]["model"] == "deepseek-v4-flash"
    client.get("/ventas/AI-0")
    assert len(calls) == 4
    updated = Sale.model_validate(store.load()["sales"]["AI-0"])
    updated.price = 10
    evaluate_and_store(updated)
    assert len(calls) == 4  # Reevaluation keeps the normalized promise and does not explain yet.
    client.get("/ventas/AI-0")
    assert len(calls) == 5
    monkeypatch.setenv("LLM_DISABLE", "1")
    response = client.get("/ventas/AI-0")
    assert llm.UNAVAILABLE in response.text and len(calls) == 5
    assert client.get("/salud").json()["llm"] == "determinista"


def test_fabricated_explanation_and_invalid_json_fall_back(monkeypatch):
    mock_http(monkeypatch, {"text": "RETENER por R99_inventada y pérdida real de S/ 99999."})
    sale = Sale(id="V-TEST", phone="900000001", plan="fibra_850", price=59.5)
    verdict = evaluate(sale, Context())
    text = llm.explain_verdict(sale, verdict)
    assert verdict.decision in text and "R99" not in text and "99999" not in text
    assert llm.describe()["provider"] == "determinista"
    monkeypatch.setattr(llm.httpx.Client, "post", lambda *a, **k: httpx.Response(
        200, request=httpx.Request("POST", "https://example.invalid"), json={
            "choices": [{"message": {"content": "not json"}}]}))
    promise, mode = llm.normalize_promise("S/ 59.50", load_config("catalog"))
    assert mode == "determinista" and promise.price == 59.5


def test_batch_summary_accepts_the_computed_row_count(monkeypatch):
    mock_http(monkeypatch, {"text": "Se evaluaron 2 ventas."})
    sale = Sale(id="DEMO", phone="900000001", plan="fibra_850", price=59.5)
    rows = [{"sale": sale, "verdict": evaluate(sale, Context())}] * 2
    assert llm.summarize_batch(rows) == "Se evaluaron 2 ventas."
    assert llm.describe()["provider"] == "OpenCode Go"
