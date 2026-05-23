import re
from datetime import date
from typing import Optional


MONTHS_ID = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4,
    "mei": 5, "juni": 6, "juli": 7, "agustus": 8,
    "september": 9, "oktober": 10, "november": 11, "desember": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "agu": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12,
}

MONTHS_EN = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

ALL_MONTHS = {**MONTHS_ID, **MONTHS_EN}


def _safe_date(year: int, month: int, day: int) -> Optional[str]:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def _normalize_year(year: int) -> int:
    if year < 100:
        return year + (2000 if year < 50 else 1900)
    return year


def extract_dates(text: str) -> list[str]:
    """
    Extract dates from text. Returns sorted list of ISO format dates (YYYY-MM-DD).
    Default interpretation for dd/mm/yyyy is DAY/MONTH/YEAR (Indonesian/European).
    """
    if not text:
        return []

    found: set[str] = set()
    text_lower = text.lower()

    # Format: dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy
    for m in re.finditer(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b", text):
        day, month, year = int(m.group(1)), int(m.group(2)), _normalize_year(int(m.group(3)))
        d = _safe_date(year, month, day)
        if d:
            found.add(d)

    # Format: yyyy-mm-dd (ISO)
    for m in re.finditer(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text):
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        d = _safe_date(year, month, day)
        if d:
            found.add(d)

    month_pattern = "|".join(sorted(ALL_MONTHS.keys(), key=len, reverse=True))

    # Format: dd Month yyyy (ID & EN), separator: space or hyphen
    for m in re.finditer(
        rf"\b(\d{{1,2}})[\s\-]+({month_pattern})[\s\-]+(\d{{2,4}})\b",
        text_lower,
    ):
        day = int(m.group(1))
        month = ALL_MONTHS[m.group(2)]
        year = _normalize_year(int(m.group(3)))
        d = _safe_date(year, month, day)
        if d:
            found.add(d)

    # Format: Month dd, yyyy (EN)
    for m in re.finditer(
        rf"\b({month_pattern})\s+(\d{{1,2}}),?\s+(\d{{4}})\b",
        text_lower,
    ):
        month = ALL_MONTHS[m.group(1)]
        day = int(m.group(2))
        year = int(m.group(3))
        d = _safe_date(year, month, day)
        if d:
            found.add(d)

    return sorted(found)