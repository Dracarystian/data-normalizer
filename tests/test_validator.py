import pytest

from normalizer.exceptions import NormalizationError
from normalizer.validator import Validator

SCHEMA = {
    "schema": "test",
    "version": "1.0",
    "fields": {
        "bill_id": {"type": "string", "required": True},
        "submitted_date": {"type": "date", "required": True},
        "status": {"type": "enum", "required": True, "values": ["draft", "approved"]},
        "title": {"type": "string", "required": False},
        "amount": {"type": "integer", "required": False},
    },
}


class TestValidator:
    def test_valid_record_passes(self):
        v = Validator()
        v.validate(
            {"bill_id": "PL-001", "submitted_date": "2026-01-01", "status": "draft"},
            SCHEMA,
        )

    def test_missing_required_field_raises(self):
        v = Validator()
        with pytest.raises(NormalizationError) as exc_info:
            v.validate({"submitted_date": "2026-01-01", "status": "draft"}, SCHEMA)
        assert exc_info.value.field == "bill_id"

    def test_empty_string_required_raises(self):
        v = Validator()
        with pytest.raises(NormalizationError) as exc_info:
            v.validate(
                {"bill_id": "  ", "submitted_date": "2026-01-01", "status": "draft"}, SCHEMA
            )
        assert exc_info.value.field == "bill_id"

    def test_none_required_raises(self):
        v = Validator()
        with pytest.raises(NormalizationError) as exc_info:
            v.validate(
                {"bill_id": None, "submitted_date": "2026-01-01", "status": "draft"}, SCHEMA
            )
        assert exc_info.value.field == "bill_id"

    def test_invalid_enum_value_raises(self):
        v = Validator()
        with pytest.raises(NormalizationError) as exc_info:
            v.validate(
                {"bill_id": "PL-001", "submitted_date": "2026-01-01", "status": "unknown"},
                SCHEMA,
            )
        assert exc_info.value.field == "status"

    def test_wrong_type_raises(self):
        v = Validator()
        with pytest.raises(NormalizationError) as exc_info:
            v.validate(
                {"bill_id": "PL-001", "submitted_date": "2026-01-01", "status": "draft", "amount": "not-a-number"},
                SCHEMA,
            )
        assert exc_info.value.field == "amount"

    def test_optional_none_passes(self):
        v = Validator()
        v.validate(
            {"bill_id": "PL-001", "submitted_date": "2026-01-01", "status": "draft", "title": None},
            SCHEMA,
        )

    def test_error_has_raw_value(self):
        v = Validator()
        with pytest.raises(NormalizationError) as exc_info:
            v.validate(
                {"bill_id": "PL-001", "submitted_date": "2026-01-01", "status": "bad_value"},
                SCHEMA,
            )
        assert exc_info.value.raw_value == "bad_value"
