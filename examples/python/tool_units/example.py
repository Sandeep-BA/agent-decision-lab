# Author: Sandeep Belgavi. Original synthetic quantity contract.
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass

UNITS = {"s": ("time", Decimal("1")),
         "ms": ("time", Decimal("0.001")),
         "B": ("data", Decimal("1")),
         "KiB": ("data", Decimal("1024"))}

@dataclass(frozen=True)
class Quantity:
    dimension: str
    magnitude: Decimal

def quantity(value, unit):
    if not isinstance(value, str) or not isinstance(unit, str) or unit not in UNITS:
        raise ValueError("explicit decimal text and a supported unit required")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid decimal") from exc
    if not number.is_finite() or number < 0:
        raise ValueError("quantity must be finite and nonnegative")
    dimension, scale = UNITS[unit]
    return Quantity(dimension, number * scale)

def add(left, right):
    if left.dimension != right.dimension:
        raise ValueError("incompatible dimensions")
    return Quantity(left.dimension, left.magnitude + right.magnitude)

assert add(quantity("250", "ms"), quantity("1.5", "s")).magnitude == Decimal("1.750")
assert quantity("2", "KiB").magnitude == Decimal("2048")


def run_demo(fixture):
    result = add(quantity(*fixture[0]), quantity(*fixture[1]))
    return {"dimension":result.dimension,"magnitude":str(result.magnitude)}

if __name__ == "__main__":
    import json
    from pathlib import Path
    fixture = json.loads(Path(__file__).with_name("sample-input.json").read_text(encoding="utf-8"))
    print(json.dumps(run_demo(fixture),sort_keys=True))
