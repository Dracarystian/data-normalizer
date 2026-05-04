from datetime import datetime
from typing import Any

from .exceptions import NormalizationError

_PYTHON_TYPES: dict[str, type | tuple] = {
    "string": str,
    "integer": int,
    "float": (int, float),
    "boolean": bool,
    "date": str,
    "enum": str,
}


class Validator:
    def validate(self, data: dict[str, Any], schema: dict) -> None:
        fields_schema = schema.get("fields", {})

        for field_name, field_def in fields_schema.items():
            value = data.get(field_name)
            required = field_def.get("required", False)

            if value is None or (isinstance(value, str) and value.strip() == ""):
                if required:
                    raise NormalizationError(
                        field_name,
                        "Campo requerido ausente o vacío",
                        value,
                    )
                continue

            field_type = field_def.get("type", "string")
            expected = _PYTHON_TYPES.get(field_type)

            if expected and not isinstance(value, expected):
                raise NormalizationError(
                    field_name,
                    f"Tipo incorrecto: esperado {field_type}, recibido {type(value).__name__}",
                    value,
                )

            if field_type == "enum":
                allowed = field_def.get("values", [])
                if value not in allowed:
                    raise NormalizationError(
                        field_name,
                        f"Valor enum '{value}' no está en los valores permitidos: {allowed}",
                        value,
                    )

            # D6: verify that date strings are actually valid ISO dates (YYYY-MM-DD).
            # The transformer normalises the format, but a corrupted string can still
            # reach the validator if a custom mapper produces one.
            if field_type == "date":
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except (ValueError, TypeError):
                    raise NormalizationError(
                        field_name,
                        f"Fecha '{value}' no es un ISO8601 válido (YYYY-MM-DD)",
                        value,
                    )

            # D5: enforce max_length on string fields.
            if field_type == "string":
                max_length = field_def.get("max_length")
                if max_length is not None and len(value) > max_length:
                    raise NormalizationError(
                        field_name,
                        f"Cadena excede max_length={max_length}: largo actual={len(value)}",
                        value,
                    )

            # D4: enforce numeric range constraints.
            if field_type in ("integer", "float"):
                min_val = field_def.get("min")
                max_val = field_def.get("max")
                if min_val is not None and value < min_val:
                    raise NormalizationError(
                        field_name,
                        f"Valor {value} es menor al mínimo permitido {min_val}",
                        value,
                    )
                if max_val is not None and value > max_val:
                    raise NormalizationError(
                        field_name,
                        f"Valor {value} es mayor al máximo permitido {max_val}",
                        value,
                    )
