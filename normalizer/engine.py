import logging
from datetime import datetime, timezone
from typing import Any

from .exceptions import InvalidMapperError, NormalizationError
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

# D7: structured logging — callers configure handlers; the library only emits.
logger = logging.getLogger(__name__)


class Normalizer:
    def __init__(self, schema: str, mapper: str):
        schema_loader = SchemaLoader()
        mapper_loader = MapperLoader()

        self._schema = schema_loader.load(schema)
        self._mapper = mapper_loader.load(mapper)

        # S2: verify the mapper was written for the schema being loaded.
        declared = self._mapper.get("schema")
        actual = self._schema.get("schema")
        if declared != actual:
            raise InvalidMapperError(
                f"El mapper declara schema='{declared}' pero se cargó schema='{actual}'"
            )

        self._transformer = Transformer()
        self._validator = Validator()
        logger.debug(
            "Normalizer inicializado: schema=%s source=%s",
            actual,
            self._mapper.get("source"),
        )

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        logger.debug(
            "Normalizando registro: schema=%s source=%s",
            self._schema.get("schema"),
            self._mapper.get("source"),
        )
        transformed = self._transformer.apply(raw, self._mapper, self._schema)
        self._validator.validate(transformed, self._schema)

        transformed["_meta"] = {
            "normalizer_version": _VERSION,
            "normalized_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": self._mapper.get("source"),
            "schema": self._schema.get("schema"),
        }

        return transformed

    def normalize_batch(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize multiple records without stopping on the first error.

        Returns a list parallel to `records`. Each entry is a dict with:
          - ``result``: normalized record, or ``None`` if normalization failed.
          - ``error``: ``NormalizationError`` instance, or ``None`` on success.
        """
        # D3: batch processing that collects per-record errors instead of fail-fast.
        results = []
        ok = errors = 0
        for i, record in enumerate(records):
            try:
                result = self.normalize(record)
                results.append({"result": result, "error": None})
                ok += 1
            except NormalizationError as e:
                results.append({"result": None, "error": e})
                errors += 1
                logger.warning("Error en registro %d: [%s] %s", i, e.field, e.reason)

        logger.info(
            "Batch completado: %d ok, %d errores de %d registros",
            ok,
            errors,
            len(records),
        )
        return results
