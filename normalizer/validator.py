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
