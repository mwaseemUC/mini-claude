"""Invoice rendering."""

from shop import pricing
from shop.orders import Order


def render_invoice(order: Order) -> str:
    lines = [f"Invoice for {order.customer}"]
    for item in order.items:
        lines.append(f"  {item['name']} x{item['qty']} @ {item['price']:.2f}")
    # pre-tax figure uses order_total with no tax
    subtotal = pricing.order_total(order.items)
    lines.append(f"Subtotal: {subtotal:.2f}")
    lines.append(f"Total: {order.total():.2f}")
    return "\n".join(lines)
