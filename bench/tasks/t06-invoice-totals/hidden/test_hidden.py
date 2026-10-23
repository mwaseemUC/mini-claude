import subprocess
import sys
from pathlib import Path

import report

EXPECTED = """INV-1001 59.51
INV-1002 1.61
INV-1003 44.94
INV-1004 0.00
INV-1005 1.10
INV-1006 11.43
INV-1007 49.50
INV-1008 3.71
""".splitlines()


def test_cli_output_matches_accounting():
    r = subprocess.run(
        [sys.executable, "report.py"], capture_output=True, text=True, timeout=30
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == EXPECTED


def test_compute_totals_on_other_data(tmp_path):
    p = Path(tmp_path) / "other.csv"
    p.write_text(
        "id,qty,unit_price,discount,tax_pct\n"
        "X,1,0.10,0,5\n"  # tax 0.005 rounds half up to 0.01
        "Y,3,0.335,0,0\n"  # 1.005 rounds half up to 1.01
        "Z,1,10.00,3.00,10\n"  # discount comes off before tax
        "W,2,5.00,10.00,8\n"  # discount equal to the subtotal -> 0.00
        "V,1,9.99,25.00,8\n"  # discount larger than subtotal -> clamped at 0.00
        "U,1,2.675,0,0\n",  # 2.675 is below the representable half in floats; must be 2.68
        encoding="utf-8",
    )
    assert report.compute_totals(str(p)) == {
        "X": "0.11",
        "Y": "1.01",
        "Z": "7.70",
        "W": "0.00",
        "V": "0.00",
        "U": "2.68",
    }
