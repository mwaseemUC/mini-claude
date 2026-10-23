"""Print the total for every invoice in invoices.csv, one per line: `ID TOTAL`."""

import csv
import sys


def compute_totals(path: str) -> dict[str, str]:
    totals = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            gross = int(row["qty"]) * float(row["unit_price"])
            with_tax = gross * (1 + float(row["tax_pct"]) / 100)
            total = round(with_tax - float(row["discount"]), 2)
            totals[row["id"]] = f"{total:.2f}"
    return totals


def main(path: str = "invoices.csv") -> None:
    for invoice_id, total in compute_totals(path).items():
        print(f"{invoice_id} {total}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
