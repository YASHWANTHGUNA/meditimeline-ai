from risk_engine import compute_risk_flags


def lab(title, value, date="2026-10-11", t="Lab Result", text=None, status="unknown"):
    return {"event_id": f"e_{title}", "event_type": t, "title": title, "date": date,
            "lab": {"test_name": title, "value": value, "value_text": text, "status": status}}


def test_no_events_is_routine():
    r = compute_risk_flags([])
    assert r["overall_level"] == "routine" and r["flags"] == []


def test_bp_and_family_history_compound():
    events = [
        lab("Blood Pressure", None, t="Vital Sign", text="145/92"),
        {"event_id": "fh", "event_type": "Family History", "title": "Maternal coronary artery disease", "description": ""},
    ]
    r = compute_risk_flags(events)
    cats = [f["category"] for f in r["flags"]]
    assert "Blood pressure" in cats and "Family history" in cats
    assert r["overall_level"] == "soon"


def test_latest_reading_wins_and_crisis_is_prompt():
    events = [lab("Total Cholesterol", 250, date="2025-01-01"), lab("Total Cholesterol", 180, date="2026-10-01"),
              lab("Blood Pressure", None, t="Vital Sign", text="185/125")]
    r = compute_risk_flags(events)
    assert not any(f["category"] == "Cholesterol" for f in r["flags"])
    assert r["overall_level"] == "prompt"


def test_inflammation_markers_flagged_from_report_status():
    events = [lab("C-Reactive Protein (CRP)", 32, status="high"), lab("ESR", 48, status="high")]
    r = compute_risk_flags(events)
    assert any(f["category"] == "Inflammation markers" for f in r["flags"])
    assert r["overall_level"] == "soon"


def test_normal_vitals_only_give_routine_or_none():
    events = [lab("Blood Pressure", None, t="Vital Sign", text="118/76"), lab("BMI", 22.0, t="Vital Sign")]
    assert compute_risk_flags(events)["flags"] == []