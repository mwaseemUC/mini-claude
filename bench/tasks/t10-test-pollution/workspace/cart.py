"""A shopping cart with promo codes."""

DISCOUNT_CODES = {"SAVE10": 0.10, "HALF": 0.50}


class Cart:
    applied_codes: list[str] = []

    def __init__(self, items=[]):
        self.items = items

    def add(self, name: str, price: float, qty: int = 1) -> None:
        self.items.append({"name": name, "price": price, "qty": qty})

    def count(self) -> int:
        return sum(i["qty"] for i in self.items)

    def apply_code(self, code: str) -> None:
        if code not in DISCOUNT_CODES:
            raise ValueError(f"unknown code {code!r}")
        if code in self.applied_codes:
            raise ValueError(f"code {code!r} already applied")
        self.applied_codes.append(code)

    def total(self) -> float:
        subtotal = sum(i["price"] * i["qty"] for i in self.items)
        for code in self.applied_codes:
            subtotal *= 1 - DISCOUNT_CODES[code]
        return round(subtotal, 2)
