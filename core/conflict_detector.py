import json
from collections import defaultdict
from typing import Optional

from utils.date_extractor import extract_dates
from utils.logger import get_logger

logger = get_logger(__name__)


# Conflict types and severities (sesuai spec algoritma)
CONFLICT_TEMPORAL = "TEMPORAL_CONFLICT"
CONFLICT_VALUE = "VALUE_CONFLICT"
CONFLICT_MULTI_SOURCE = "MULTI_SOURCE"

SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"


class ConflictDetector:
    """
    Detects conflicts across retrieved documents for a given query.

    Types:
    - TEMPORAL_CONFLICT (HIGH): documents disagree on dates for related events
    - VALUE_CONFLICT (HIGH): documents state different numeric/factual values
    - MULTI_SOURCE (MEDIUM): same topic discussed in many docs (may indicate
      inconsistency even without direct contradiction)

    Complexity: O(k*m) where k=docs, m=facts per doc
    """

    # Pattern for numeric-with-unit (currency, percentage, plain number)
    # Examples: "Rp 50.000.000", "50 juta", "Rp50.000", "25%", "1500 orang"
    _NUMBER_PATTERNS = [
        # Currency Rp
        (r"(?:Rp\.?\s*)([\d.,]+(?:\s*(?:juta|ribu|miliar|milyar|triliun|jt|rb|m))?)", "currency_rp"),
        # USD
        (r"(?:\$|USD\s*)([\d.,]+(?:\s*(?:million|thousand|billion|k|m|b))?)", "currency_usd"),
        # Percentage
        (r"([\d.,]+)\s*%", "percentage"),
        # Indonesian number-with-magnitude
        (r"\b(\d+(?:[.,]\d+)?)\s+(juta|ribu|miliar|milyar|triliun)\b", "magnitude_id"),
    ]

    def __init__(self):
        import re
        self._compiled = [
            (re.compile(pat, re.IGNORECASE), label)
            for pat, label in self._NUMBER_PATTERNS
        ]

    # ---------- Helpers: extraction per document ----------

    def _extract_doc_dates(self, doc: dict) -> list[str]:
        """Return ISO dates from doc.text (or pre-stored dates field if present)."""
        # Prefer pre-extracted dates if available
        stored = doc.get("dates")
        if stored:
            if isinstance(stored, str):
                try:
                    return list(json.loads(stored))
                except (json.JSONDecodeError, TypeError):
                    pass
            elif isinstance(stored, list):
                return list(stored)
        # Fallback: extract on the fly
        return extract_dates(doc.get("text", ""))

    def _extract_doc_values(self, doc: dict) -> list[dict]:
        """Return list of {raw, label, normalized} from doc text."""
        text = doc.get("text", "")
        if not text:
            return []

        values = []
        for pattern, label in self._compiled:
            for m in pattern.finditer(text):
                raw = m.group(0).strip()
                inner = m.group(1).strip() if m.lastindex and m.lastindex >= 1 else raw
                normalized = self._normalize_value(inner, label)
                if normalized is not None:
                    values.append({
                        "raw": raw,
                        "label": label,
                        "normalized": normalized,
                    })
        return values

    def _normalize_value(self, raw: str, label: str) -> Optional[float]:
        """Normalize raw number string to float. Returns None if unparseable."""
        try:
            s = raw.lower().strip()

            # Magnitude multiplier (Indonesian)
            multiplier = 1.0
            id_units = {
                "triliun": 1e12, "miliar": 1e9, "milyar": 1e9,
                "juta": 1e6, "jt": 1e6, "ribu": 1e3, "rb": 1e3,
            }
            en_units = {
                "billion": 1e9, "million": 1e6, "thousand": 1e3,
                "b": 1e9, "m": 1e6, "k": 1e3,
            }

            for unit, mult in {**id_units, **en_units}.items():
                if s.endswith(" " + unit) or s.endswith(unit):
                    multiplier = mult
                    s = s.rsplit(unit, 1)[0].strip()
                    break

            # Clean separators (handle both 1.000,50 and 1,000.50)
            # Heuristic: if both . and , present, the rightmost is decimal
            if "." in s and "," in s:
                if s.rfind(",") > s.rfind("."):
                    s = s.replace(".", "").replace(",", ".")
                else:
                    s = s.replace(",", "")
            elif "," in s:
                # Indonesian decimal comma if 1-2 digits after, else thousands sep
                parts = s.split(",")
                if len(parts) == 2 and len(parts[1]) <= 2:
                    s = s.replace(",", ".")
                else:
                    s = s.replace(",", "")
            else:
                # Only dots: could be thousands sep (Indo) or decimal (US)
                # If exactly 3 digits after each dot -> thousands separator
                if s.count(".") >= 1:
                    parts_dot = s.split(".")
                    # All non-last parts must be digits, last part exactly 3 digits -> thousands
                    if all(len(p) == 3 and p.isdigit() for p in parts_dot[1:]):
                        s = s.replace(".", "")

            return float(s) * multiplier
        except (ValueError, AttributeError):
            return None

    # ---------- Detectors ----------

    def _detect_temporal(self, docs: list[dict]) -> list[dict]:
        """
        TEMPORAL_CONFLICT: different docs mention different dates.
        We flag when >=2 distinct dates appear across >=2 different docs.
        """
        if len(docs) < 2:
            return []

        date_to_docs: dict[str, set] = defaultdict(set)
        for doc in docs:
            doc_id = doc.get("doc_id", doc.get("filename", "unknown"))
            for d in self._extract_doc_dates(doc):
                date_to_docs[d].add(doc_id)

        if len(date_to_docs) < 2:
            return []

        # Collect docs involved
        all_dates = sorted(date_to_docs.keys())
        affected_doc_ids = set()
        for docs_set in date_to_docs.values():
            affected_doc_ids.update(docs_set)

        if len(affected_doc_ids) < 2:
            return []

        return [{
            "conflict_type": CONFLICT_TEMPORAL,
            "severity": SEVERITY_HIGH,
            "description": (
                f"Documents reference {len(all_dates)} different dates: "
                f"{', '.join(all_dates)}. Verify which date applies to the query."
            ),
            "affected_docs": sorted(str(d) for d in affected_doc_ids),
            "details": {"dates": all_dates},
        }]

    def _detect_value(self, docs: list[dict]) -> list[dict]:
        """
        VALUE_CONFLICT: different docs mention different values of the same label
        (e.g., one doc says "Rp 50 juta", another says "Rp 75 juta").
        """
        if len(docs) < 2:
            return []

        # Group values by label across docs
        label_to_entries: dict[str, list[tuple]] = defaultdict(list)
        # entry: (doc_id, raw, normalized)
        for doc in docs:
            doc_id = doc.get("doc_id", doc.get("filename", "unknown"))
            for v in self._extract_doc_values(doc):
                label_to_entries[v["label"]].append((doc_id, v["raw"], v["normalized"]))

        conflicts = []
        for label, entries in label_to_entries.items():
            if len(entries) < 2:
                continue

            # Unique normalized values across DIFFERENT docs
            doc_to_values: dict = defaultdict(set)
            for doc_id, raw, norm in entries:
                doc_to_values[doc_id].add(round(norm, 4))

            if len(doc_to_values) < 2:
                continue

            all_unique_values = set()
            for vals in doc_to_values.values():
                all_unique_values.update(vals)

            if len(all_unique_values) < 2:
                continue

            # Significant difference: ratio between max/min > 1.1 (>10% difference)
            vmax, vmin = max(all_unique_values), min(all_unique_values)
            if vmin > 0 and (vmax / vmin) < 1.1:
                continue

            raws = sorted({e[1] for e in entries})
            affected = sorted({str(e[0]) for e in entries})

            conflicts.append({
                "conflict_type": CONFLICT_VALUE,
                "severity": SEVERITY_HIGH,
                "description": (
                    f"Documents disagree on {label} values: {', '.join(raws)}. "
                    f"Range: {vmin:g} to {vmax:g}."
                ),
                "affected_docs": affected,
                "details": {"label": label, "values": sorted(all_unique_values)},
            })

        return conflicts

    def _detect_multi_source(self, docs: list[dict]) -> list[dict]:
        """
        MULTI_SOURCE: same topic spread across many high-similarity docs.
        Heuristic: >=3 docs all above similarity 0.5 -> medium warning.
        """
        if len(docs) < 3:
            return []
        high_sim = [d for d in docs if d.get("similarity", 0) >= 0.5]
        if len(high_sim) < 3:
            return []

        affected = sorted(str(d.get("doc_id", d.get("filename", "?"))) for d in high_sim)
        return [{
            "conflict_type": CONFLICT_MULTI_SOURCE,
            "severity": SEVERITY_MEDIUM,
            "description": (
                f"Topic appears across {len(high_sim)} documents with high relevance. "
                f"Cross-check answer against multiple sources."
            ),
            "affected_docs": affected,
            "details": {"doc_count": len(high_sim)},
        }]

    # ---------- Public API ----------

    def detect(self, docs: list[dict]) -> dict:
        """
        Main entry point.
        Input: list of doc dicts with at least {doc_id|filename, text, similarity, dates?}
        Returns: {
            "has_conflict": bool,
            "conflicts": [list of conflict dicts],
            "summary": str,
        }
        """
        if not docs:
            return {"has_conflict": False, "conflicts": [], "summary": "no documents"}

        conflicts = []
        conflicts.extend(self._detect_temporal(docs))
        conflicts.extend(self._detect_value(docs))
        conflicts.extend(self._detect_multi_source(docs))

        # Sort by severity (HIGH > MEDIUM > LOW)
        severity_order = {SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 1, SEVERITY_LOW: 2}
        conflicts.sort(key=lambda c: severity_order.get(c["severity"], 99))

        has_conflict = any(c["severity"] in (SEVERITY_HIGH, SEVERITY_MEDIUM) for c in conflicts)

        if not conflicts:
            summary = "No conflicts detected"
        else:
            high = sum(1 for c in conflicts if c["severity"] == SEVERITY_HIGH)
            med = sum(1 for c in conflicts if c["severity"] == SEVERITY_MEDIUM)
            summary = f"{len(conflicts)} conflict(s): {high} HIGH, {med} MEDIUM"

        logger.info(f"Conflict detection: {summary}")
        return {
            "has_conflict": has_conflict,
            "conflicts": conflicts,
            "summary": summary,
        }


_detector: Optional[ConflictDetector] = None


def get_conflict_detector() -> ConflictDetector:
    global _detector
    if _detector is None:
        _detector = ConflictDetector()
    return _detector