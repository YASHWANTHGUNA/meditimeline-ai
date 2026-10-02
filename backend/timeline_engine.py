from datetime import datetime
from typing import List
from schemas import TimelineEvent

def parse_flexible_date(date_str: str) -> datetime:
    """
    Attempts to parse various date formats returned by LLMs into a standard datetime object 
    for accurate chronological sorting. Defaults to a distant past date if unparseable.
    """
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%B %Y",
        "%b %Y",
        "%Y"
    ]
    
    cleaned_date = date_str.strip()
    for fmt in formats:
        try:
            return datetime.strptime(cleaned_date, fmt)
        except ValueError:
            continue
            
    # Fallback for descriptive or unparseable clinical timeframes (e.g. "Childhood", "Unknown")
    return datetime(1900, 1, 1)

def sort_and_normalize_timeline(events: List[TimelineEvent]) -> List[TimelineEvent]:
    """
    Sorts a list of clinical events chronologically based on their normalized dates.
    Latest events or oldest first? Timelines are typically displayed oldest to newest.
    """
    sorted_events = sorted(
        events, 
        key=lambda e: parse_flexible_date(e.date)
    )
    return sorted_events