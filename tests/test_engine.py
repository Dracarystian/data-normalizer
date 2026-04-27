import json
from pathlib import Path

import pytest

from normalizer import Normalizer, NormalizationError

FIXTURES = Path(__file__).parent / "fixtures"
SCHEMAS = Path(__file__).parent.parent / "examples/dapper/schemas"
MAPPERS = Path(__file__).parent.parent / "examples/dapper/mappers"

SCHEMA_BILL = str(SCHEMAS / "legislative_bill.yaml")
MAPPER_COLOMBIA = str(MAPPERS / "colombia_legislative_bill.yaml")
MAPPER_SPAIN = str(MAPPERS / "spain_legislative_bill.yaml")


@pytest.fixture
def colombia_records():
    with open(FIXTURES / "raw_colombia.json") as f:
        return json.load(f)


@pytest.fixture
def spain_records():
    with open(FIXTURES / "raw_spain.json") as f:
        return json.load(f)


@pytest.fixture
def normalizer_colombia():
    return Normalizer(schema=SCHEMA_BILL, mapper=MAPPER_COLOMBIA)


@pytest.fixture
def normalizer_spain():
    return Normalizer(schema=SCHEMA_BILL, mapper=MAPPER_SPAIN)


class TestEngineColumbia:
    def test_normalize_basic(self, normalizer_colombia, colombia_records):
        result = normalizer_colombia.normalize(colombia_records[0])
        assert result["bill_id"] == "PL-123-2026"
        assert result["submitted_date"] == "2026-03-15"
        assert result["status"] == "in_review"
        assert result["country"] == "CO"

    def test_normalize_approved(self, normalizer_colombia, colombia_records):
        result = normalizer_colombia.normalize(colombia_records[1])
        assert result["status"] == "approved"
        assert result["submitted_date"] == "2026-01-01"

    def test_normalize_null_optional_field(self, normalizer_colombia, colombia_records):
        result = normalizer_colombia.normalize(colombia_records[2])
        assert result["status"] == "rejected"
        assert result.get("title") is None

    def test_meta_keys_present(self, normalizer_colombia, colombia_records):
        result = normalizer_colombia.normalize(colombia_records[0])
        assert "_meta" in result
        assert result["_meta"]["source"] == "colombia"
        assert result["_meta"]["schema"] == "legislative_bill"
        assert "normalized_at" in result["_meta"]
        assert "normalizer_version" in result["_meta"]

    def test_missing_required_field_raises(self, normalizer_colombia):
        bad_record = {"fecha": "01/01/2026", "estado": "Aprobado", "titulo": "Test"}
        # radicado (bill_id) is missing
        with pytest.raises(NormalizationError) as exc_info:
            normalizer_colombia.normalize(bad_record)
        assert exc_info.value.field == "bill_id"

    def test_unknown_enum_raises(self, normalizer_colombia):
        bad_record = {
            "radicado": "PL-001",
            "fecha": "01/01/2026",
            "estado": "Estado desconocido",
            "titulo": "Test",
        }
        with pytest.raises(NormalizationError) as exc_info:
            normalizer_colombia.normalize(bad_record)
        assert exc_info.value.field == "status"


class TestEngineSpain:
    def test_normalize_basic(self, normalizer_spain, spain_records):
        result = normalizer_spain.normalize(spain_records[0])
        assert result["bill_id"] == "121/000042"
        assert result["submitted_date"] == "2026-02-10"
        assert result["status"] == "in_review"
        assert result["country"] == "ES"

    def test_fixed_country_value(self, normalizer_spain, spain_records):
        for record in spain_records:
            result = normalizer_spain.normalize(record)
            assert result["country"] == "ES"
