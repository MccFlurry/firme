"""No developer credentials or network calls in the test suite."""

import pytest

from engine import llm


@pytest.fixture(autouse=True)
def offline_providers(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENCODE_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_DISABLE", raising=False)
    monkeypatch.setattr(llm, "AUTH_PATH", tmp_path / "auth.json")
    monkeypatch.setattr(llm.httpx.Client, "post", lambda *a, **k: pytest.fail("Unexpected network call"))
    token = llm._USED_PROVIDER.set(None)
    yield
    llm._USED_PROVIDER.reset(token)
