import pytest
from fastapi.testclient import TestClient
import main


class FakeCursor:
    def __init__(self, docs): self.docs = docs
    async def to_list(self, length=None): return self.docs


class FakeEvents:
    def __init__(self, docs): self.docs = docs
    def find(self, q, proj=None):
        return FakeCursor([d for d in self.docs if d.get("patient_id") == q.get("patient_id")])


class FakeDB:
    def __init__(self, docs): self.events = FakeEvents(docs)


@pytest.fixture
def client(monkeypatch):
    docs = [{"patient_id": "P1", "event_id": "e1", "event_type": "Vital Sign", "title": "Blood Pressure",
             "date": "2026-10-13", "lab": {"test_name": "Blood Pressure", "value_text": "150/95", "status": "high"}}]
    monkeypatch.setattr(main, "db", FakeDB(docs))
    return TestClient(main.app)  # no `with`: skips lifespan (no real Mongo needed)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_timeline_endpoint(client):
    r = client.get("/patients/P1/timeline").json()
    assert r["patient_id"] == "P1" and r["total_events"] == 1


def test_risk_flags_endpoint(client):
    r = client.get("/patients/P1/risk-flags").json()
    assert r["overall_level"] == "soon" and r["flags"][0]["category"] == "Blood pressure"
    assert "not a diagnosis" in r["disclaimer"]


def test_risk_flags_unknown_patient_404(client):
    assert client.get("/patients/NOPE/risk-flags").status_code == 404