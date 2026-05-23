from datetime import datetime, timezone
from typing import Any, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    meta: Optional[dict] = None,
) -> dict:
    response: dict = {
        "success": True,
        "timestamp": _now_iso(),
    }
    if message is not None:
        response["message"] = message
    if data is not None:
        response["data"] = data
    if meta is not None:
        response["meta"] = meta
    return response


def error_response(
    message: str,
    code: Optional[str] = None,
    details: Optional[dict] = None,
    status_code: int = 400,
) -> tuple[dict, int]:
    response: dict = {
        "success": False,
        "timestamp": _now_iso(),
        "error": {"message": message},
    }
    if code is not None:
        response["error"]["code"] = code
    if details is not None:
        response["error"]["details"] = details
    return response, status_code


def build_query_response(
    answer: str,
    sources: list[dict],
    confidence: float,
    has_conflict: bool = False,
    conflict_details: Optional[list[dict]] = None,
    hallucination: Optional[dict] = None,
    execution_time_ms: Optional[float] = None,
) -> dict:
    data: dict = {
        "answer": answer,
        "sources": sources,
        "confidence": round(float(confidence), 4),
        "has_conflict": has_conflict,
    }
    if conflict_details:
        data["conflict_details"] = conflict_details
    if hallucination is not None:
        data["hallucination"] = hallucination
    if execution_time_ms is not None:
        data["execution_time_ms"] = round(float(execution_time_ms), 2)
    return success_response(data=data)