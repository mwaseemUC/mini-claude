"""Print the total for every invoice in invoices.csv, one per line: `ID TOTAL`."""

import csv
import sys
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def compute_totals(path: str) -> dict[str, str]:
    totals = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            gross = int(row["qty"]) * Decimal(row["unit_price"])
            net = max(gross - Decimal(row["discount"]), Decimal(0))
            tax = (net * Decimal(row["tax_pct"]) / 100).quantize(CENT, ROUND_HALF_UP)
            totals[row["id"]] = f"{(net + tax).quantize(CENT, ROUND_HALF_UP):.2f}"
    return totals


def main(path: str = "invoices.csv") -> None:
    for invoice_id, total in compute_totals(path).items():
        print(f"{invoice_id} {total}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
