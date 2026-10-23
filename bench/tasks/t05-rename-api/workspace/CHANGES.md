# Planned change: rename `calc_total` to `order_total`

`shop.pricing.calc_total` has a misleading name (it is used for whole orders, not single
calculations). Rename it.

Requirements:

1. The function is now called `order_total`, in the same module (`shop/pricing.py`), with the
   same signature and behaviour.
2. Keep `calc_total` importable from `shop.pricing` as a deprecated alias so external code does
   not break. Calling it must:
   - emit a `DeprecationWarning` whose message mentions `order_total`,
   - attribute the warning to the caller's line (use `stacklevel=2`),
   - return exactly what `order_total` returns for the same arguments.
3. Nothing inside the `shop` package may call the deprecated name any more. Using the package
   normally (building orders, rendering invoices) must not emit any `DeprecationWarning`.
4. Update the docstrings and comments that mention the old name.
