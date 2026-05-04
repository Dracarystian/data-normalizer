import json
from pathlib import Path

import pytest

from normalizer import Normalizer, NormalizationError
from normalizer.exceptions import InvalidMapperError, InvalidSchemaError

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


class TestNormalizeBatch:
    def test_batch_returns_result_per_record(self, normalizer_colombia, colombia_records):
        # D3: normalize_batch must return one entry per input record
        results = normalizer_colombia.normalize_batch(colombia_records)
        assert len(results) == len(colombia_records)

    def test_batch_ok_records_have_result(self, normalizer_colombia, colombia_records):
        results = normalizer_colombia.normalize_batch(colombia_records)
        for entry in results:
            assert entry["result"] is not None
            assert entry["error"] is None

    def test_batch_bad_record_captured_not_raised(self, normalizer_colombia, colombia_records):
        bad = {"fecha": "01/01/2026", "estado": "Aprobado"}  # missing radicado
        mixed = [colombia_records[0], bad]
        results = normalizer_colombia.normalize_batch(mixed)
        assert results[0]["error"] is None
        assert results[1]["error"] is not None
        assert isinstance(results[1]["error"], NormalizationError)
        assert results[1]["result"] is None

    def test_batch_error_does_not_stop_remaining(self, normalizer_colombia, colombia_records):
        bad = {"fecha": "01/01/2026", "estado": "Aprobado"}  # missing radicado
        records = [bad, colombia_records[0], bad, colombia_records[1]]
        results = normalizer_colombia.normalize_batch(records)
        assert results[1]["error"] is None
        assert results[3]["error"] is None


class TestSecurityChecks:
    def test_schema_mapper_mismatch_wrong_mapper(self, tmp_path):
        wrong_mapper = tmp_path / "wrong.yaml"
        wrong_mapper.write_text(
            "source: test\nschema: other_schema\nfields:\n  bill_id:\n    from: id\n"
        )
        with pytest.raises(InvalidMapperError, match="schema"):
            Normalizer(
                schema=str(SCHEMAS / "legislative_bill.yaml"),
                mapper=str(wrong_mapper),
            )

    def test_loader_rejects_non_yaml_extension(self, tmp_path):
        # S3: files with non-.yaml/.yml extensions must be rejected
        bad_file = tmp_path / "schema.json"
        bad_file.write_text("{}")
        with pytest.raises(InvalidSchemaError, match="Extensión"):
            Normalizer(schema=str(bad_file), mapper=str(MAPPERS / "colombia_legislative_bill.yaml"))

    def test_error_message_truncates_long_raw_value(self, normalizer_colombia):
        # S1: raw_value in the error string must be truncated (no full PII dump)
        long_value = "X" * 200
        record = {
            "radicado": long_value,
            "fecha": "01/01/2026",
            "estado": "Estado desconocido",
        }
        with pytest.raises(NormalizationError) as exc_info:
            normalizer_colombia.normalize(record)
        assert len(str(exc_info.value)) < 300
        assert exc_info.value.raw_value == "Estado desconocido"  # full value still accessible


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
