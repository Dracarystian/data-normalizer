from pathlib import Path
from typing import Any

import yaml

from .exceptions import (
    InvalidMapperError,
    InvalidSchemaError,
    MapperNotFoundError,
    SchemaNotFoundError,
)

VALID_FIELD_TYPES = {"string", "integer", "float", "boolean", "date", "enum"}


def _load_yaml(path: str, not_found_exc, invalid_exc) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise not_found_exc(f"Archivo no encontrado: {path}")
    try:
        with p.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise invalid_exc(f"Error parseando YAML en {path}: {e}")
    if not isinstance(data, dict):
        raise invalid_exc(f"El archivo YAML debe ser un diccionario: {path}")
    return data


class SchemaLoader:
    def load(self, path: str) -> dict[str, Any]:
        data = _load_yaml(path, SchemaNotFoundError, InvalidSchemaError)
        self._validate(data, path)
        return data

    def _validate(self, data: dict, path: str) -> None:
        for key in ("schema", "version", "fields"):
            if key not in data:
                raise InvalidSchemaError(f"Schema en '{path}' falta clave requerida: '{key}'")
        if not isinstance(data["fields"], dict):
            raise InvalidSchemaError(f"'fields' debe ser un diccionario en '{path}'")
        for field_name, field_def in data["fields"].items():
            if not isinstance(field_def, dict):
                raise InvalidSchemaError(f"Campo '{field_name}' debe ser un diccionario en '{path}'")
            if "type" not in field_def:
                raise InvalidSchemaError(f"Campo '{field_name}' no tiene 'type' en '{path}'")
            if field_def["type"] not in VALID_FIELD_TYPES:
                raise InvalidSchemaError(
                    f"Campo '{field_name}' tiene tipo inválido '{field_def['type']}' en '{path}'. "
                    f"Válidos: {VALID_FIELD_TYPES}"
                )
            if field_def["type"] == "enum" and "values" not in field_def:
                raise InvalidSchemaError(
                    f"Campo enum '{field_name}' debe definir 'values' en '{path}'"
                )


class MapperLoader:
    def load(self, path: str) -> dict[str, Any]:
        data = _load_yaml(path, MapperNotFoundError, InvalidMapperError)
        self._validate(data, path)
        return data

    def _validate(self, data: dict, path: str) -> None:
        for key in ("source", "schema", "fields"):
            if key not in data:
                raise InvalidMapperError(f"Mapper en '{path}' falta clave requerida: '{key}'")
        if not isinstance(data["fields"], dict):
            raise InvalidMapperError(f"'fields' debe ser un diccionario en '{path}'")
        for field_name, field_def in data["fields"].items():
            if not isinstance(field_def, dict):
                raise InvalidMapperError(
                    f"Campo '{field_name}' debe ser un diccionario en '{path}'"
                )
            if "from" not in field_def and "value" not in field_def:
                raise InvalidMapperError(
                    f"Campo '{field_name}' debe tener 'from' o 'value' en '{path}'"
                )

        extra_fields = data.get("extra_fields", {})
        if not isinstance(extra_fields, dict):
            raise InvalidMapperError(f"'extra_fields' debe ser un diccionario en '{path}'")
        for field_name, field_def in extra_fields.items():
            if not isinstance(field_def, dict):
                raise InvalidMapperError(
                    f"extra_fields.'{field_name}' debe ser un diccionario en '{path}'"
                )
            if "from" not in field_def and "value" not in field_def:
                raise InvalidMapperError(
                    f"extra_fields.'{field_name}' debe tener 'from' o 'value' en '{path}'"
                )
