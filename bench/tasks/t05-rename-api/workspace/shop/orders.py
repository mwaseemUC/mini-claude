"""Orders."""

from shop.pricing import calc_total


class Order:
    def __init__(self, customer: str, tax_rate: float = 0.0):
        self.customer = customer
        self.tax_rate = tax_rate
        self.items: list[dict] = []

    def add(self, name: str, price: float, qty: int = 1) -> None:
        self.items.append({"name": name, "price": price, "qty": qty})

    def total(self) -> float:
        # delegates to calc_total
        return calc_total(self.items, self.tax_rate)
