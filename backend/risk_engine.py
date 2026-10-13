"""
risk_engine.py - rule-based preventive risk flags over a patient's extracted events.

Design rules (matches the problem statement):
  * NEVER diagnoses. Findings are phrased as "reading is above the usual range".
  * Deterministic and explainable: every flag cites the event it came from.
  * Thresholds follow common published guideline cut-offs (AHA BP, ATP III lipids,
    ADA glucose/HbA1c, WHO BMI). They are screening aids, not clinical advice.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

LEVELS = {"routine": 0, "soon": 1, "prompt": 2}
LEVEL_NAMES = {v: k for k, v in LEVELS.items()}

DISCLAIMER = (
    "This is an automated preventive screening aid, not a diagnosis. "
    "It cannot replace a clinician. If you feel severe symptoms (for example severe chest pain, "
    "trouble breathing, fainting), seek emergency care immediately."
)

_MEASURE_TYPES = ("Lab Result", "Vital Sign")


def _lab(ev: dict) -> dict:
    return ev.get("lab") or {}


def _name(ev: dict) -> str:
    return f"{_lab(ev).get('test_name') or ''} {ev.get('title') or ''}".lower()


def _number(ev: dict) -> Optional[float]:
    lab = _lab(ev)
    v = lab.get("value")
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"-?\d+(?:\.\d+)?", lab.get("value_text") or "")
    return float(m.group()) if m else None


def _bp_pair(ev: dict) -> Optional[Tuple[int, int]]:
    for text in (_lab(ev).get("value_text"), ev.get("description"), (ev.get("source") or {}).get("source_text")):
        m = re.search(r"(\d{2,3})\s*/\s*(\d{2,3})", text or "")
        if m:
            return int(m.group(1)), int(m.group(2))
    return None


def _latest(events: List[dict], pattern: str, bp: bool = False) -> Optional[dict]:
    rx = re.compile(pattern)
    hits = [
        e for e in events
        if e.get("event_type") in _MEASURE_TYPES and rx.search(_name(e))
        and ((_bp_pair(e) is not None) if bp else (_number(e) is not None))
    ]
    if not hits:
        return None
    hits.sort(key=lambda e: e.get("date") or "")
    return hits[-1]


def compute_risk_flags(events: List[dict]) -> Dict[str, Any]:
    flags: List[dict] = []

    def add(category: str, finding: str, level: str, rec: str, ev: Optional[dict] = None):
        flags.append({
            "category": category,
            "finding": finding,
            "level": level,
            "recommendation": rec,
            "event_id": (ev or {}).get("event_id"),
            "date": (ev or {}).get("date") or (ev or {}).get("original_date_str"),
        })

    # --- Blood pressure -------------------------------------------------
    ev = _latest(events, r"blood pressure|\bbp\b", bp=True)
    if ev:
        s, d = _bp_pair(ev)
        txt = f"{s}/{d} mmHg"
        if s >= 180 or d >= 120:
            add("Blood pressure", f"Reading {txt} is in a very high range.", "prompt",
                "Seek medical evaluation promptly; recheck after resting 5 minutes.", ev)
        elif s >= 140 or d >= 90:
            add("Blood pressure", f"Reading {txt} is in the high range.", "soon",
                "Book a clinician visit, log home readings twice daily, reduce sodium (DASH-style eating).", ev)
        elif s >= 120 or d >= 80:
            add("Blood pressure", f"Reading {txt} is above the optimal (<120/80) range.", "routine",
                "Limit sodium, stay active, and recheck at your next routine visit.", ev)

    # --- Lipids ----------------------------------------------------------
    ev = _latest(events, r"total cholesterol|cholesterol,? total")
    if ev:
        v = _number(ev)
        if v >= 240:
            add("Cholesterol", f"Total cholesterol {v:g} mg/dL is high (>=240).", "soon",
                "Discuss a lipid management plan with a clinician.", ev)
        elif v >= 200:
            add("Cholesterol", f"Total cholesterol {v:g} mg/dL is borderline high (200-239).", "routine",
                "Favour fibre, limit saturated fat, add regular activity; recheck in ~3 months.", ev)
    ev = _latest(events, r"\bldl")
    if ev:
        v = _number(ev)
        if v >= 190:
            add("LDL cholesterol", f"LDL {v:g} mg/dL is very high (>=190).", "soon",
                "Discuss this result with a clinician soon.", ev)
        elif v >= 160:
            add("LDL cholesterol", f"LDL {v:g} mg/dL is high (160-189).", "soon",
                "Discuss diet and treatment options with a clinician.", ev)
        elif v >= 130:
            add("LDL cholesterol", f"LDL {v:g} mg/dL is borderline high (130-159).", "routine",
                "Diet and activity changes; re-test lipids in ~90 days.", ev)
    ev = _latest(events, r"\bhdl")
    if ev:
        v = _number(ev)
        if v < 40:
            add("HDL cholesterol", f"HDL {v:g} mg/dL is low (<40).", "routine",
                "Regular aerobic exercise and not smoking help raise HDL.", ev)
    ev = _latest(events, r"triglycerid")
    if ev:
        v = _number(ev)
        if v >= 500:
            add("Triglycerides", f"Triglycerides {v:g} mg/dL are very high (>=500).", "prompt",
                "Seek medical evaluation promptly.", ev)
        elif v >= 200:
            add("Triglycerides", f"Triglycerides {v:g} mg/dL are high (200-499).", "soon",
                "Reduce sugars/alcohol and discuss with a clinician.", ev)
        elif v >= 150:
            add("Triglycerides", f"Triglycerides {v:g} mg/dL are borderline high (150-199).", "routine",
                "Cut refined carbs and alcohol; stay active.", ev)

    # --- Glucose ---------------------------------------------------------
    ev = _latest(events, r"glucose")
    if ev:
        v = _number(ev)
        if v >= 126:
            add("Blood glucose", f"Glucose {v:g} mg/dL is in a high range (>=126 fasting).", "soon",
                "Ask a clinician about confirmatory testing (e.g. HbA1c).", ev)
        elif v >= 100:
            add("Blood glucose", f"Glucose {v:g} mg/dL is above the normal fasting range (100-125).", "routine",
                "Reduce sugary foods, increase activity, and recheck within a few months.", ev)
    ev = _latest(events, r"hba1c|a1c")
    if ev:
        v = _number(ev)
        if v >= 6.5:
            add("HbA1c", f"HbA1c {v:g}% is in a high range (>=6.5).", "soon",
                "Discuss this result with a clinician for confirmation and follow-up.", ev)
        elif v >= 5.7:
            add("HbA1c", f"HbA1c {v:g}% is above the normal range (5.7-6.4).", "routine",
                "Lifestyle changes (diet, activity, weight) can help; recheck in about a year.", ev)

    # --- Body mass index -------------------------------------------------
    ev = _latest(events, r"\bbmi\b|body mass")
    if ev:
        v = _number(ev)
        if v >= 30:
            add("Weight (BMI)", f"BMI {v:g} is in the obesity range (>=30).", "routine",
                "A structured diet/activity plan or clinician guidance can help.", ev)
        elif v >= 25:
            add("Weight (BMI)", f"BMI {v:g} is above the healthy range (25-29.9).", "routine",
                "Gradual weight reduction lowers long-term cardiovascular risk.", ev)

    # --- Kidney markers flagged by the report itself ----------------------
    kidney = [
        e for e in events
        if e.get("event_type") in _MEASURE_TYPES and re.search(r"creatinine|\bbun\b|urea|egfr", _name(e))
        and _lab(e).get("status") in ("high", "low", "critical")
    ]
    if kidney:
        names = ", ".join(sorted({(_lab(e).get("test_name") or e.get("title")) for e in kidney}))
        add("Kidney markers", f"{names} outside the reference range in the report.", "soon",
            "Follow up with a clinician and keep blood pressure well controlled.", kidney[-1])

    # --- Symptoms worth attention ----------------------------------------
    for e in events:
        if e.get("event_type") == "Symptom" and re.search(
            r"chest|dyspn|shortness of breath|palpitation|syncope|faint", f"{e.get('title')} {e.get('description')}".lower()
        ):
            add("Symptoms", f"Report mentions: {e.get('title')}.", "soon",
                "Recurring or worsening chest/breathing symptoms should be evaluated by a clinician; "
                "seek emergency care if severe.", e)
            break

    # --- Family history compounding --------------------------------------
    fh_text = " ".join(
        f"{e.get('title')} {e.get('description')}".lower() for e in events if e.get("event_type") == "Family History"
    )
    cardio_fh = re.search(r"coronary|heart|cardiac|myocardial|stroke|hypertension", fh_text)
    diabetes_fh = re.search(r"diabet", fh_text)
    cats = {f["category"] for f in flags}
    if cardio_fh and cats & {"Blood pressure", "Cholesterol", "LDL cholesterol", "Triglycerides"}:
        add("Family history", "Family history of heart disease together with the above readings raises long-term risk.",
            "soon", "Mention your family history at your next visit; earlier and more frequent screening may be advised.")
    if diabetes_fh and cats & {"Blood glucose", "HbA1c", "Weight (BMI)"}:
        add("Family history", "Family history of diabetes together with the above readings raises long-term risk.",
            "soon", "Mention your family history to your clinician; consider yearly glucose/HbA1c checks.")

    top = max((LEVELS[f["level"]] for f in flags), default=0)
    summaries = {
        0: "No notable preventive concerns found in the uploaded records." if not flags
           else "A few readings are slightly outside optimal ranges; lifestyle steps are suggested.",
        1: "Some findings are worth discussing with a clinician in the coming weeks.",
        2: "Some findings suggest seeing a clinician promptly.",
    }
    flags.sort(key=lambda f: -LEVELS[f["level"]])
    return {
        "overall_level": LEVEL_NAMES[top],
        "summary": summaries[top],
        "flags": flags,
        "events_analyzed": len(events),
        "disclaimer": DISCLAIMER,
    }