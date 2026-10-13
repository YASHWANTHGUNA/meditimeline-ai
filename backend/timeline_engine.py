import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

MONTH_MAP = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3, "april": 4, "apr": 4,
    "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7, "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9, "october": 10, "oct": 10, "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


def is_valid_date(year: int, month: int, day: int) -> bool:
    try:
        datetime(year, month, day)
        return True
    except ValueError:
        return False


def parse_and_normalize_date(date_str: Optional[str]) -> Tuple[Optional[str], Optional[str], str]:
    if not date_str or not isinstance(date_str, str):
        return None, None, "undated"
    clean_str = date_str.strip().strip(",.").strip()
    if not clean_str or clean_str.lower() in ["unknown", "n/a", "none", "undated", "childhood", "past history"]:
        return None, None, "undated"

    m = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", clean_str)
    if m:
        y, m_str, d_str = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if is_valid_date(y, m_str, d_str):
            return f"{y:04d}-{m_str:02d}-{d_str:02d}", f"{y:04d}-{m_str:02d}-{d_str:02d}", "day"

    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", clean_str)
    if m:
        d_str, m_str, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if is_valid_date(y, m_str, d_str):
            return f"{y:04d}-{m_str:02d}-{d_str:02d}", f"{y:04d}-{m_str:02d}-{d_str:02d}", "day"

    m1 = re.match(r"^([a-zA-Z]+)\s+(\d{1,2})[,\s]+(\d{4})$", clean_str)
    m2 = re.match(r"^(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})$", clean_str)
    if m1 or m2:
        if m1:
            month_name, day_str, year_str = m1.groups()
        else:
            day_str, month_name, year_str = m2.groups()
        m_code = MONTH_MAP.get(month_name.lower())
        if m_code and is_valid_date(int(year_str), m_code, int(day_str)):
            return f"{int(year_str):04d}-{m_code:02d}-{int(day_str):02d}", f"{int(year_str):04d}-{m_code:02d}-{int(day_str):02d}", "day"

    m = re.match(r"^([a-zA-Z]+)\s+(\d{4})$", clean_str)
    if m:
        month_name, year_str = m.groups()
        m_code = MONTH_MAP.get(month_name.lower())
        if m_code:
            return f"{int(year_str):04d}-{m_code:02d}-01", f"{int(year_str):04d}-{m_code:02d}", "month"

    m = re.match(r"^(\d{4})$", clean_str)
    if m:
        year_str = int(m.group(1))
        return f"{year_str:04d}-01-01", f"{year_str:04d}", "year"

    return None, None, "undated"


def process_timeline_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    dated_events = []
    undated_events = []
    for idx, event in enumerate(events):
        raw_date = event.get("date") or event.get("original_date_str")
        sort_key, norm_date, precision = parse_and_normalize_date(raw_date)
        event_copy = dict(event)
        event_copy["original_date_str"] = event_copy.get("original_date_str") or raw_date
        event_copy["date_precision"] = precision
        if sort_key:
            event_copy["date"] = norm_date
            dated_events.append((sort_key, idx, event_copy))
        else:
            event_copy["date"] = None
            undated_events.append(event_copy)
    dated_events.sort(key=lambda x: (x[0], x[1]))
    sorted_dated = [item[2] for item in dated_events]
    return {
        "dated_events": sorted_dated,
        "undated_events": undated_events,
        "all_events": sorted_dated + undated_events,
        "total_events": len(events),
        "dated_count": len(sorted_dated),
        "undated_count": len(undated_events),
    }