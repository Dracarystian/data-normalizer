# data-normalizer

Domain-agnostic normalization library for heterogeneous data sources. Translates raw records from multiple origins (APIs, scrapers, CSV, RSS) into a validated canonical structure using YAML-defined schemas and mappers.

## The problem it solves

Every data pipeline that aggregates from more than one source hits the same wall: the same concept arrives with a different name, format, and vocabulary depending on who published it.

**Product catalog aggregation** is the canonical example. Pull inventory from three marketplaces and you get:

| Concept        | Amazon                 | Mercado Libre        | Shopify              |
|----------------|------------------------|----------------------|----------------------|
| Product ID     | `ASIN`                 | `id`                 | `product_id`         |
| Price          | `price.amount`         | `precio`             | `variants[0].price`  |
| Stock status   | `"In Stock"`           | `"Disponible"`       | `"active"`           |
| Published date | `2024-03-15T00:00:00Z` | `15/03/2024`         | `1710460800` (epoch) |

Before you can join, compare, or store any of this you have to write translation logic — and that logic tends to spread across ingestion scripts, dbt models, and API wrappers until nobody owns it. `data-normalizer` centralises that translation in versioned, testable YAML files.

Other datasets with the same problem: financial transactions across payment gateways (Stripe / PayPal / Mercado Pago), job listings across boards (LinkedIn / Indeed / Glassdoor), real-estate listings across portals, IoT telemetry from different device manufacturers.

## Installation

```bash
pip install git+https://github.com/usuario/data-normalizer.git@v1.0.0
```

## Quick Start

```python
from normalizer import Normalizer
from normalizer.exceptions import NormalizationError

n = Normalizer(
    schema="./schemas/product.yaml",
    mapper="./mappers/mercadolibre_product.yaml",
)

try:
    result = n.normalize(raw_record)
except NormalizationError as e:
    print(f"Campo: {e.field} | Razón: {e.reason} | Valor: {e.raw_value}")
```

The returned dict always contains a `_meta` key:

```python
{
    "product_id": "MLA-987654321",
    "title": "Laptop Dell XPS 13",
    "price": 1299.99,
    "currency": "USD",
    "stock_status": "available",
    "listed_at": "2024-03-15",
    "marketplace": "mercadolibre",
    "_meta": {
        "normalizer_version": "1.0.0",
        "normalized_at": "2026-04-27T10:00:00Z",
        "source": "mercadolibre",
        "schema": "product"
    }
}
```

## Schema YAML

Defines the canonical structure expected in the output. Write it once; every source maps into it.

```yaml
schema: product
version: "1.0"

fields:
  product_id:
    type: string
    required: true

  title:
    type: string
    required: true

  price:
    type: float
    required: true

  currency:
    type: string
    required: true

  stock_status:
    type: enum
    required: true
    values: [available, out_of_stock, discontinued]

  listed_at:
    type: date
    format: ISO8601
    required: false

  marketplace:
    type: string
    required: true
```

Supported types: `string`, `integer`, `float`, `boolean`, `date`, `enum`.

## Mapper YAML

Defines how to translate a specific source into the canonical schema. One mapper per source; the schema never changes.

**Mercado Libre:**

```yaml
source: mercadolibre
schema: product

fields:
  product_id:
    from: id                    # source field name

  title:
    from: titulo

  price:
    from: precio

  currency:
    from: moneda

  stock_status:
    from: disponibilidad
    enum_map:                   # translate source values to canonical enum values
      "Disponible":   available
      "Sin stock":    out_of_stock
      "Descontinuado": discontinued

  listed_at:
    from: fecha_publicacion
    input_format: "DD/MM/YYYY"

  marketplace:
    value: "mercadolibre"       # fixed value — does not come from source record
```

**Amazon:**

```yaml
source: amazon
schema: product

fields:
  product_id:
    from: ASIN

  title:
    from: title

  price:
    from: price.amount

  currency:
    from: price.currency

  stock_status:
    from: availability
    enum_map:
      "In Stock":           available
      "Out of Stock":       out_of_stock
      "Discontinued":       discontinued

  listed_at:
    from: date_first_available
    input_format: ISO8601

  marketplace:
    value: "amazon"
```

**Shopify:**

```yaml
source: shopify
schema: product

fields:
  product_id:
    from: product_id

  title:
    from: title

  price:
    from: variants[0].price

  currency:
    from: currency_code

  stock_status:
    from: status
    enum_map:
      "active":   available
      "draft":    out_of_stock
      "archived": discontinued

  listed_at:
    from: published_at
    input_format: ISO8601

  marketplace:
    value: "shopify"
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

When YAML rules are not enough (nested structures, computed fields, conditional logic), subclass `BaseMapper` in your own project:

```python
from normalizer.mappers import BaseMapper

class ShopifyMapper(BaseMapper):
    def map(self, raw: dict) -> dict:
        # Shopify nests price inside variants; grab the lowest active variant
        active_variants = [v for v in raw.get("variants", []) if v["inventory_policy"] != "deny"]
        price = min(float(v["price"]) for v in active_variants) if active_variants else None

        return {
            "product_id": str(raw["product_id"]),
            "title": raw["title"],
            "price": price,
            "currency": raw.get("currency_code", "USD"),
            "stock_status": self._map_status(raw["status"]),
            "listed_at": raw.get("published_at", "")[:10],
            "marketplace": "shopify",
        }

    def _map_status(self, status: str) -> str:
        return {"active": "available", "draft": "out_of_stock", "archived": "discontinued"}.get(status, "out_of_stock")
```

## Examples

See [examples/dapper/](examples/dapper/) for a complete product catalog use case with schemas and mappers for Mercado Libre, Amazon, and Shopify.

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
