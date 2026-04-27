class NormalizationError(Exception):
    def __init__(self, field: str, reason: str, raw_value=None):
        self.field = field
        self.reason = reason
        self.raw_value = raw_value
        super().__init__(f"[{field}] {reason} — valor recibido: {raw_value}")


class SchemaNotFoundError(Exception):
    pass


class MapperNotFoundError(Exception):
    pass


class InvalidSchemaError(Exception):
    pass


class InvalidMapperError(Exception):
    pass
