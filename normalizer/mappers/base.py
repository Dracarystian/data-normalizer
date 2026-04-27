from abc import ABC, abstractmethod


class BaseMapper(ABC):
    """
    Base class for programmatic mappers when YAML rules are insufficient.
    Subclass this in your own project — not inside this library.
    """

    @abstractmethod
    def map(self, raw: dict) -> dict:
        """Translate a raw source record to the canonical field structure."""
