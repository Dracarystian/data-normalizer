from datetime import datetime
from typing import Any

from .exceptions import NormalizationError

# Common date input formats tried in order when input_format is not specified
_FALLBACK_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d.%m.%Y",
]

_FORMAT_DIRECTIVES = {
    "DD": "%d",
    "MM": "%m",
    "YYYY": "%Y",
    "HH": "%H",
    "mm": "%M",
    "ss": "%S",
}


def _dapper_format_to_strptime(fmt: str) -> str:
    result = fmt
    for token, directive in _FORMAT_DIRECTIVES.items():
        result = result.replace(token, directive)
    return result


def _parse_date(value: Any, input_format: str | None, field: str) -> str:
    if value is None:
        return None

    raw = str(value).strip()

    if input_format:
        if input_format.upper() == "ISO8601":
            # Accept both date-only and datetime strings
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
                try:
                    return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            raise NormalizationError(field, f"Fecha no pudo parsearse como ISO8601: '{raw}'", raw)

        strptime_fmt = _dapper_format_to_strptime(input_format)
        try:
            return datetime.strptime(raw, strptime_fmt).strftime("%Y-%m-%d")
        except ValueError:
            raise NormalizationError(
                field,
                f"Fecha '{raw}' no coincide con formato '{input_format}'",
                raw,
            )

    for fmt in _FALLBACK_DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    raise NormalizationError(field, f"No se pudo parsear la fecha: '{raw}'", raw)


def _cast_type(value: Any, field_type: str, field: str) -> Any:
    if value is None:
        return None
    try:
        if field_type == "integer":
            # Handle numbers formatted with dots/commas as thousands separators
            cleaned = str(value).replace(".", "").replace(",", "")
            return int(cleaned)
        if field_type == "float":
            cleaned = str(value).replace(",", ".")
            return float(cleaned)
        if field_type == "boolean":
            if isinstance(value, bool):
                return value
            low = str(value).lower()
            if low in ("true", "1", "yes", "sí", "si"):
                return True
            if low in ("false", "0", "no"):
                return False
            raise ValueError(f"'{value}' no es un booleano reconocido")
        if field_type == "string":
            return str(value).strip()
    except (ValueError, TypeError) as e:
        raise NormalizationError(field, f"No se pudo convertir a {field_type}: {e}", value)
    return value


class Transformer:
    def apply(self, raw: dict, mapper: dict, schema: dict) -> dict:
        result = {}
        fields_mapper = mapper.get("fields", {})
        fields_schema = schema.get("fields", {})

        for canonical_field, field_map in fields_mapper.items():
            schema_def = fields_schema.get(canonical_field, {})
            field_type = schema_def.get("type", "string")

            # Fixed value — does not come from raw data
            if "value" in field_map:
                result[canonical_field] = self._apply_type(
                    field_map["value"], field_type, field_map, canonical_field
                )
                continue

            source_key = field_map["from"]
            raw_value = raw.get(source_key)

            result[canonical_field] = self._apply_type(
                raw_value, field_type, field_map, canonical_field
            )

        extra_fields = mapper.get("extra_fields", {})
        if extra_fields:
            result["_extra"] = self._apply_extra(raw, extra_fields)

        return result

    def _apply_extra(self, raw: dict, extra_fields: dict) -> dict:
        extra = {}
        for field_name, field_map in extra_fields.items():
            if "value" in field_map:
                extra[field_name] = str(field_map["value"]).strip()
            else:
                raw_value = raw.get(field_map["from"])
                extra[field_name] = str(raw_value).strip() if raw_value is not None else None
        return extra

    def _apply_type(self, value: Any, field_type: str, field_map: dict, field: str) -> Any:
        if field_type == "date":
            return _parse_date(value, field_map.get("input_format"), field)

        if field_type == "enum":
            enum_map = field_map.get("enum_map", {})
            if enum_map and value is not None:
                mapped = enum_map.get(str(value))
                if mapped is None:
                    raise NormalizationError(
                        field,
                        f"Valor enum '{value}' no encontrado en enum_map",
                        value,
                    )
                return mapped
            return value

        return _cast_type(value, field_type, field)
