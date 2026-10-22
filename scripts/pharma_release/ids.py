"""Lossless identity encoding. No stripping, numeric casting, or clinical mapping."""
import json


def require_identifier(value):
    if type(value) is not str or not value.strip():
        raise ValueError("Identity components must be nonblank strings; coercion is forbidden")
    return value


def qualified_id(entity, source, original_id):
    """Codec v1: entity + ':' + compact JSON [source, original_id]."""
    for part in (entity, source, original_id):
        require_identifier(part)
    if entity not in {"product", "label", "recall", "communication", "source"}:
        raise ValueError("Unsupported ID namespace")
    return entity + ":" + json.dumps([source, original_id], ensure_ascii=False, separators=(",", ":"))


def decode_id(value):
    require_identifier(value)
    entity, payload = value.split(":", 1)
    parts = json.loads(payload)
    if not isinstance(parts, list) or len(parts) != 2:
        raise ValueError("Invalid identity encoding")
    if qualified_id(entity, *parts) != value:
        raise ValueError("Identity encoding is not canonical")
    return entity, parts[0], parts[1]


def existing_id(value, entity):
    """Keep the already established ingredient/formulation name-hash ID unchanged."""
    require_identifier(value)
    prefix = entity + ":"
    digest = value.removeprefix(prefix)
    if entity not in {"ingredient", "formulation"} or not value.startswith(prefix):
        raise ValueError("Wrong existing identity namespace")
    if len(digest) != 24 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("Invalid existing identity shape")
    return value
