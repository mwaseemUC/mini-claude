import pytest

import vendorlib
from convert import to_celsius


@pytest.mark.parametrize(
    "f,c", [(212, 100.0), (32, 0.0), (-40, -40.0), (98.6, 37.0), (0, -17.777777777777779)]
)
def test_values(f, c):
    assert to_celsius(f) == pytest.approx(c, abs=1e-6)


def test_actually_uses_vendorlib(monkeypatch):
    calls = []

    def fake_convert(self, value, *, from_unit, to_unit):
        calls.append((value, from_unit, to_unit))
        return vendorlib.Measurement(42.5, to_unit)

    monkeypatch.setattr(vendorlib.Converter, "convert", fake_convert)
    assert to_celsius(100) == 42.5
    assert calls == [(100, "degF", "degC")]
