import asyncio
import pytest
from google.genai import errors

import services


def api_error(code):
    return errors.APIError(code, {"error": {"message": "x", "status": "X"}})


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    async def no_sleep(_): return None
    monkeypatch.setattr(services.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(services, "MODEL_CHAIN", ["primary", "backup"])
    monkeypatch.setattr(services, "PRIMARY_MODEL", "primary")
    monkeypatch.setattr(services, "RETRIES_PER_MODEL", 2)


def test_retries_then_succeeds(monkeypatch):
    calls = []
    async def fake(model, chunk):
        calls.append(model)
        if len(calls) < 2:
            raise api_error(503)
        return {"events": [], "metadata": {}}
    monkeypatch.setattr(services, "_call_model", fake)
    assert asyncio.run(services._extract_chunk("t")) == {"events": [], "metadata": {}}
    assert calls == ["primary", "primary"]


def test_falls_back_to_next_model(monkeypatch):
    async def fake(model, chunk):
        if model == "primary":
            raise api_error(503)
        return {"events": [{"title": "ok"}], "metadata": {}}
    monkeypatch.setattr(services, "_call_model", fake)
    assert asyncio.run(services._extract_chunk("t"))["events"][0]["title"] == "ok"


def test_non_retryable_error_raises_immediately(monkeypatch):
    calls = []
    async def fake(model, chunk):
        calls.append(model)
        raise api_error(400)
    monkeypatch.setattr(services, "_call_model", fake)
    with pytest.raises(errors.APIError):
        asyncio.run(services._extract_chunk("t"))
    assert len(calls) == 1


def test_all_models_exhausted_gives_friendly_runtime_error(monkeypatch):
    async def fake(model, chunk): raise api_error(503)
    monkeypatch.setattr(services, "_call_model", fake)
    with pytest.raises(RuntimeError, match="overloaded"):
        asyncio.run(services.extract_timeline_from_chunks(["a"]))


def test_chunk_results_merge_and_dedupe(monkeypatch):
    ev = {"event_type": "Diagnosis", "title": "HTN", "date": "2018"}
    async def fake(model, chunk):
        return {"events": [ev], "metadata": {"patient_id": "P9", "patient_name": "A"}}
    monkeypatch.setattr(services, "_call_model", fake)
    out = asyncio.run(services.extract_timeline_from_chunks(["a", "b"]))
    assert len(out["events"]) == 1 and out["metadata"]["patient_id"] == "P9"