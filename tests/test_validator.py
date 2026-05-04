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

    def test_date_invalid_string_raises(self):
        # D6: any string that is not a valid YYYY-MM-DD must be rejected
        v = Validator()
        schema = {
            "schema": "test",
            "version": "1.0",
            "fields": {"submitted_date": {"type": "date", "required": True}},
        }
        with pytest.raises(NormalizationError) as exc_info:
            v.validate({"submitted_date": "not-a-date"}, schema)
        assert exc_info.value.field == "submitted_date"

    def test_date_valid_iso_passes(self):
        v = Validator()
        schema = {
            "schema": "test",
            "version": "1.0",
            "fields": {"submitted_date": {"type": "date", "required": True}},
        }
        v.validate({"submitted_date": "2026-03-15"}, schema)

    def test_max_length_exceeded_raises(self):
        # D5: string longer than max_length must be rejected
        v = Validator()
        schema = {
            "schema": "test",
            "version": "1.0",
            "fields": {"title": {"type": "string", "required": True, "max_length": 10}},
        }
        with pytest.raises(NormalizationError) as exc_info:
            v.validate({"title": "this string is way too long"}, schema)
        assert exc_info.value.field == "title"

    def test_max_length_exact_passes(self):
        v = Validator()
        schema = {
            "schema": "test",
            "version": "1.0",
            "fields": {"title": {"type": "string", "required": True, "max_length": 5}},
        }
        v.validate({"title": "hello"}, schema)

    def test_min_value_raises(self):
        # D4: value below min must be rejected
        v = Validator()
        schema = {
            "schema": "test",
            "version": "1.0",
            "fields": {"price": {"type": "float", "required": True, "min": 0.0}},
        }
        with pytest.raises(NormalizationError) as exc_info:
            v.validate({"price": -1.0}, schema)
        assert exc_info.value.field == "price"

    def test_max_value_raises(self):
        v = Validator()
        schema = {
            "schema": "test",
            "version": "1.0",
            "fields": {"stock": {"type": "integer", "required": True, "max": 100}},
        }
        with pytest.raises(NormalizationError) as exc_info:
            v.validate({"stock": 101}, schema)
        assert exc_info.value.field == "stock"

    def test_within_range_passes(self):
        v = Validator()
        schema = {
            "schema": "test",
            "version": "1.0",
            "fields": {"stock": {"type": "integer", "required": True, "min": 0, "max": 100}},
        }
        v.validate({"stock": 50}, schema)

    def test_error_has_raw_value(self):
        v = Validator()
        with pytest.raises(NormalizationError) as exc_info:
            v.validate(
                {"bill_id": "PL-001", "submitted_date": "2026-01-01", "status": "bad_value"},
                SCHEMA,
            )
        assert exc_info.value.raw_value == "bad_value"
