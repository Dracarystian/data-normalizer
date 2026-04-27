import pytest

from normalizer.exceptions import NormalizationError
from normalizer.transformer import Transformer

SCHEMA = {
    "schema": "test",
    "version": "1.0",
    "fields": {
        "start_date": {"type": "date"},
        "amount": {"type": "integer"},
        "rate": {"type": "float"},
        "active": {"type": "boolean"},
        "label": {"type": "string"},
        "status": {"type": "enum", "values": ["open", "closed"]},
        "country": {"type": "string"},
    },
}

MAPPER_BASE = {
    "source": "test",
    "schema": "test",
    "fields": {},
}


def make_mapper(fields: dict) -> dict:
    return {**MAPPER_BASE, "fields": fields}


class TestDateTransformation:
    def test_dd_mm_yyyy(self):
        t = Transformer()
        mapper = make_mapper({"start_date": {"from": "raw_date", "input_format": "DD/MM/YYYY"}})
        result = t.apply({"raw_date": "15/03/2026"}, mapper, SCHEMA)
        assert result["start_date"] == "2026-03-15"

    def test_iso8601(self):
        t = Transformer()
        mapper = make_mapper({"start_date": {"from": "raw_date", "input_format": "ISO8601"}})
        result = t.apply({"raw_date": "2026-03-15"}, mapper, SCHEMA)
        assert result["start_date"] == "2026-03-15"

    def test_fallback_autodetect(self):
        t = Transformer()
        mapper = make_mapper({"start_date": {"from": "raw_date"}})
        result = t.apply({"raw_date": "2026-03-15"}, mapper, SCHEMA)
        assert result["start_date"] == "2026-03-15"

    def test_invalid_date_raises(self):
        t = Transformer()
        mapper = make_mapper({"start_date": {"from": "raw_date", "input_format": "DD/MM/YYYY"}})
        with pytest.raises(NormalizationError) as exc_info:
            t.apply({"raw_date": "not-a-date"}, mapper, SCHEMA)
        assert exc_info.value.field == "start_date"


class TestTypeCoercion:
    def test_integer_with_dot_separator(self):
        t = Transformer()
        mapper = make_mapper({"amount": {"from": "valor"}})
        result = t.apply({"valor": "50.000"}, mapper, SCHEMA)
        assert result["amount"] == 50000

    def test_float(self):
        t = Transformer()
        mapper = make_mapper({"rate": {"from": "tasa"}})
        result = t.apply({"tasa": "3,14"}, mapper, SCHEMA)
        assert result["rate"] == pytest.approx(3.14)

    def test_boolean_truthy(self):
        t = Transformer()
        mapper = make_mapper({"active": {"from": "vigente"}})
        for val in ("true", "1", "yes", "sí"):
            result = t.apply({"vigente": val}, mapper, SCHEMA)
            assert result["active"] is True

    def test_boolean_falsy(self):
        t = Transformer()
        mapper = make_mapper({"active": {"from": "vigente"}})
        for val in ("false", "0", "no"):
            result = t.apply({"vigente": val}, mapper, SCHEMA)
            assert result["active"] is False


class TestEnumMapping:
    def test_enum_map_applied(self):
        t = Transformer()
        mapper = make_mapper({
            "status": {
                "from": "estado",
                "enum_map": {"Abierto": "open", "Cerrado": "closed"},
            }
        })
        result = t.apply({"estado": "Abierto"}, mapper, SCHEMA)
        assert result["status"] == "open"

    def test_unknown_enum_raises(self):
        t = Transformer()
        mapper = make_mapper({
            "status": {
                "from": "estado",
                "enum_map": {"Abierto": "open"},
            }
        })
        with pytest.raises(NormalizationError) as exc_info:
            t.apply({"estado": "Desconocido"}, mapper, SCHEMA)
        assert exc_info.value.field == "status"


class TestFixedValue:
    def test_value_field_ignores_raw(self):
        t = Transformer()
        mapper = make_mapper({"country": {"value": "CO"}})
        result = t.apply({"country": "ignored"}, mapper, SCHEMA)
        assert result["country"] == "CO"
