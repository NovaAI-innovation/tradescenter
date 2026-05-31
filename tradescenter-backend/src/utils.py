from datetime import date, datetime
from typing import Any

from flask import jsonify


def error_response(message: str, status_code: int = 400):
    return jsonify({"error": message}), status_code


def parse_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def iso_or_none(value: Any):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def normalize_record(record: dict | None) -> dict | None:
    if record is None:
        return None

    normalized: dict[str, Any] = {}
    for key, value in record.items():
        normalized[key] = iso_or_none(value)
    return normalized

