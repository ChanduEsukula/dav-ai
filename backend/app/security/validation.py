"""Bounded wire parsing shared by the isolated authorization verifiers."""

import json
import re
from datetime import datetime, timezone


# Keep the exception in its own module to avoid parser/verifier import cycles.
class AuthorizationRejected(ValueError):
    """A staging authorization did not pass verification."""


def parse_document(payload: bytes, *, limit: int, label: str, duplicate: str) -> dict:
    if type(payload) is not bytes or not 0 < len(payload) <= limit:
        raise AuthorizationRejected(f"Invalid {label} payload size")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise AuthorizationRejected(duplicate)
            result[key] = value
        return result

    def constant(value):
        raise AuthorizationRejected("Invalid JSON constant")

    try:
        # Require UTF-8 rather than accepting json.loads' UTF-16/32 autodetection.
        result = json.loads(payload.decode("utf-8"), object_pairs_hook=pairs,
                            parse_constant=constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, AuthorizationRejected):
            raise
        raise AuthorizationRejected(f"Invalid {label} JSON") from exc
    if not isinstance(result, dict):
        raise AuthorizationRejected(f"Invalid {label} document")
    return result


def utc_time(value: datetime) -> datetime:
    try:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise AuthorizationRejected("Verification clock lacks timezone")
        return value.astimezone(timezone.utc)
    except (ValueError, OverflowError) as exc:
        raise AuthorizationRejected("Invalid verification clock") from exc


def parse_timestamp(value: str) -> datetime:
    # A deliberately narrow RFC3339 profile; no local dates, week dates or spaces.
    if not isinstance(value, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
        r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})", value
    ):
        raise AuthorizationRejected("Invalid authorization timestamp")
    try:
        # datetime normalizes out-of-range offset minutes, so check them explicitly.
        if value[-1] != "Z" and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
            raise ValueError("Invalid UTC offset")
        return utc_time(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except (ValueError, OverflowError) as exc:
        raise AuthorizationRejected("Invalid authorization timestamp") from exc


def check_signature_input(signature: bytes) -> None:
    if type(signature) is not bytes or len(signature) != 64:
        raise AuthorizationRejected("Invalid Ed25519 signature")
