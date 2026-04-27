from datetime import datetime, timezone
from typing import Any

from .loader import MapperLoader, SchemaLoader
from .transformer import Transformer
from .validator import Validator

try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        _VERSION = version("data-normalizer")
    except PackageNotFoundError:
        _VERSION = "dev"
except ImportError:
    _VERSION = "dev"


class Normalizer:
    def __init__(self, schema: str, mapper: str):
        schema_loader = SchemaLoader()
        mapper_loader = MapperLoader()

        self._schema = schema_loader.load(schema)
        self._mapper = mapper_loader.load(mapper)
        self._transformer = Transformer()
        self._validator = Validator()

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        transformed = self._transformer.apply(raw, self._mapper, self._schema)
        self._validator.validate(transformed, self._schema)

        transformed["_meta"] = {
            "normalizer_version": _VERSION,
            "normalized_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": self._mapper.get("source"),
            "schema": self._schema.get("schema"),
        }

        return transformed
