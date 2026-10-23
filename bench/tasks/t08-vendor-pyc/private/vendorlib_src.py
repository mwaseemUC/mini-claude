"""vendorlib: unit conversion toolkit (vendored, compiled only).

Usage:

    conv = vendorlib.Converter(unit_system="si")
    m = conv.convert(212.0, from_unit="degF", to_unit="degC")
    m.magnitude   # 100.0
    m.unit        # "degC"

Notes:
  * Converter needs unit_system="si" for temperature work; "us" only knows lengths.
  * Temperature unit names are "degF", "degC" and "K" (case sensitive).
  * convert() takes from_unit and to_unit as keyword-only arguments and returns a
    Measurement. Read the number from Measurement.magnitude.
"""

__all__ = ["Converter", "Measurement", "UnitError"]

_TEMPS = {"degF", "degC", "K"}
_LENGTHS = {"m", "ft"}


class UnitError(ValueError):
    """Raised for unknown units or an unsupported unit system."""


class Measurement:
    """A number with a unit. The number is in .magnitude."""

    def __init__(self, magnitude, unit):
        self.magnitude = magnitude
        self.unit = unit

    def __repr__(self):
        return f"Measurement({self.magnitude!r}, {self.unit!r})"


def _to_kelvin(value, unit):
    if unit == "K":
        return value
    if unit == "degC":
        return value + 273.15
    return (value - 32.0) * 5.0 / 9.0 + 273.15


def _from_kelvin(kelvin, unit):
    if unit == "K":
        return kelvin
    if unit == "degC":
        return kelvin - 273.15
    return (kelvin - 273.15) * 9.0 / 5.0 + 32.0


class Converter:
    """Converts values between units of one unit system.

    Converter(unit_system="si") handles temperatures (degF, degC, K).
    Converter(unit_system="us") handles lengths (m, ft) only.
    """

    def __init__(self, *, unit_system):
        if unit_system not in ("si", "us"):
            raise UnitError(f"unknown unit_system {unit_system!r}")
        self.unit_system = unit_system

    def convert(self, value, *, from_unit, to_unit):
        """Convert value from from_unit to to_unit and return a Measurement."""
        if self.unit_system == "si":
            if from_unit not in _TEMPS or to_unit not in _TEMPS:
                raise UnitError(f"unsupported temperature unit: {from_unit!r} -> {to_unit!r}")
            return Measurement(_from_kelvin(_to_kelvin(value, from_unit), to_unit), to_unit)
        if from_unit not in _LENGTHS or to_unit not in _LENGTHS:
            raise UnitError(f"unsupported length unit: {from_unit!r} -> {to_unit!r}")
        metres = value if from_unit == "m" else value * 0.3048
        return Measurement(metres if to_unit == "m" else metres / 0.3048, to_unit)
