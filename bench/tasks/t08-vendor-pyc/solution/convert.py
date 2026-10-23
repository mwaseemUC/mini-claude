"""Temperature helpers built on the vendored vendorlib."""

import vendorlib


def to_celsius(fahrenheit: float) -> float:
    conv = vendorlib.Converter(unit_system="si")
    return conv.convert(fahrenheit, from_unit="degF", to_unit="degC").magnitude
