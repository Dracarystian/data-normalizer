class NormalizationError(Exception):
    def __init__(self, field: str, reason: str, raw_value=None):
        self.field = field
        self.reason = reason
        self.raw_value = raw_value
        # S1: truncate raw_value in the log message to avoid PII leakage.
        # The full value is still accessible via the .raw_value attribute.
        display = repr(raw_value)
        if len(display) > 80:
            display = display[:77] + "..."
        super().__init__(f"[{field}] {reason} — valor recibido: {display}")


class SchemaNotFoundError(Exception):
    pass


class MapperNotFoundError(Exception):
    pass


class InvalidSchemaError(Exception):
    pass


class InvalidMapperError(Exception):
    pass
