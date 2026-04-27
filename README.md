# data-normalizer

Domain-agnostic normalization library for heterogeneous data sources. Translates raw records from multiple origins (APIs, scrapers, CSV, RSS) into a validated canonical structure using YAML-defined schemas and mappers.

## Installation

```bash
pip install git+https://github.com/usuario/data-normalizer.git@v1.0.0
```

## Quick Start

```python
from normalizer import Normalizer
from normalizer.exceptions import NormalizationError

n = Normalizer(
    schema="./schemas/legislative_bill.yaml",
    mapper="./mappers/colombia_legislative_bill.yaml",
)

try:
    result = n.normalize(raw_record)
except NormalizationError as e:
    print(f"Campo: {e.field} | Razón: {e.reason} | Valor: {e.raw_value}")
```

The returned dict always contains a `_meta` key:

```python
{
    "bill_id": "PL-123-2026",
    "submitted_date": "2026-03-15",
    "status": "in_review",
    "country": "CO",
    "_meta": {
        "normalizer_version": "1.0.0",
        "normalized_at": "2026-04-27T10:00:00Z",
        "source": "colombia",
        "schema": "legislative_bill"
    }
}
```

## Schema YAML

Defines the canonical structure expected in the output.

```yaml
schema: legislative_bill
version: "1.0"

fields:
  bill_id:
    type: string
    required: true

  submitted_date:
    type: date
    format: ISO8601
    required: true

  status:
    type: enum
    required: true
    values: [draft, in_review, approved, rejected]

  country:
    type: string
    required: true
```

Supported types: `string`, `integer`, `float`, `boolean`, `date`, `enum`.

## Mapper YAML

Defines how to translate a specific source into the canonical schema.

```yaml
source: colombia
schema: legislative_bill

fields:
  bill_id:
    from: radicado           # source field name

  submitted_date:
    from: fecha
    input_format: "DD/MM/YYYY"   # or ISO8601

  status:
    from: estado
    enum_map:                # translate source values to canonical enum values
      "Segundo debate": in_review
      "Aprobado":       approved
      "Archivado":      rejected

  country:
    value: "CO"              # fixed value — does not come from source record
```

## Error Handling

`NormalizationError` is raised on the first failing field. It carries:

| Attribute   | Description                        |
|-------------|------------------------------------|
| `field`     | Canonical field name that failed   |
| `reason`    | Human-readable explanation         |
| `raw_value` | Original value received            |

Other exceptions: `SchemaNotFoundError`, `MapperNotFoundError`, `InvalidSchemaError`, `InvalidMapperError`.

## Custom Python Mappers

When YAML rules are not enough, subclass `BaseMapper` in your own project:

```python
from normalizer.mappers import BaseMapper

class MyComplexMapper(BaseMapper):
    def map(self, raw: dict) -> dict:
        return {
            "bill_id": self._extract_id(raw),
            ...
        }
```

## Examples

See [examples/dapper/](examples/dapper/) for a complete legislative bills use case with schemas and mappers for Colombia, Spain, and Mexico.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Versioning

Follows [Semantic Versioning](https://semver.org). Pin the version in your requirements:

```
data-normalizer @ git+https://github.com/usuario/data-normalizer.git@v1.0.0
```
