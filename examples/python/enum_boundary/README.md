# Enum values at the boundary between an agent and a service

**Author: Sandeep Belgavi**

A runnable companion to *Enum Values Between Agents and Existing Services: Near Misses and New Statuses*
(aicassindra.com, System design). It contrasts the fictional Belgavi's Book Store returns API's old compatibility
layer, which silently maps unknown reasons to `changed_mind`, with a strict write path that maps synonyms through
an explicit alias table and refuses everything else with a typed payload listing the accepted values. On the
read side, an unseen order status (`partially_shipped`) parses to `UNKNOWN` with the raw value, the service's
coarse category and a label, where a Java-style `valueOf` reader throws.

## Prerequisites

- Python 3.11 or newer. Standard library only; `requirements.txt` is intentionally empty.
- `.env.example` documents that nothing is read from the environment. No model is called.

## Commands

```
python examples/python/enum_boundary/enum_boundary.py
python -m unittest discover -s examples/python/enum_boundary -p "test_*.py"
```

## Expected output

```
{"sent": "Damaged", "legacy": "damaged", "strict": {"ok": true, "order_id": "BK-301", "reason": "damaged"}}
{"sent": "damaged_in_transit", "legacy": "changed_mind", "strict": {"ok": true, "order_id": "BK-301", "reason": "damaged"}}
{"sent": "DAMAGED", "legacy": "damaged", "strict": {"ok": true, "order_id": "BK-301", "reason": "damaged"}}
{"sent": "water_damage", "legacy": "changed_mind", "strict": {"ok": false, "error": "unknown_enum_value", "field": "return_reason", "value": "water_damage", "allowed": ["changed_mind", "damaged", "not_as_described", "wrong_item"]}}
{"value": "UNKNOWN", "raw": "partially_shipped", "category": "in_transit", "label": "First parcel shipped, second parcel being packed"}
```

## Limitations

The services are in-memory functions. Versioned value sets (a request header or API version that controls
which statuses a caller receives) are described in the article but not implemented here. The alias table is an
example; in a real system it is reviewed like code and never extended with fuzzy matching.
