# Cart Service

A standalone Python utility module that provides `CartService`, a minimal shopping cart
that tracks items (name, price, quantity) and computes order totals.

## API

- `add_item(name, price, quantity=1)` — add an item to the cart. `name` must be a non-empty
  string, `price` a non-negative number, and `quantity` a positive integer; invalid input
  raises `TypeError` or `ValueError` and nothing is added to the cart.
- `calculate_total(discount_percent=0.0)` — total price of the cart after applying a
  percentage discount. `discount_percent` must be a number between 0 and 100.
- `apply_coupon(coupon_code)` — total price of the cart after applying a promo code. Supported
  codes are `WELCOME10` (10%), `VIP20` (20%) and `FLASH50` (50%); codes are matched ignoring
  case and surrounding whitespace. A non-string code raises `TypeError`, and an empty or
  unrecognized code raises `ValueError`. The cart is never modified.
- `update_quantity(item_name, new_quantity)` — set the quantity of an item already in the cart
  and return a copy of the updated item. `item_name` must be a string and `new_quantity` an
  integer, otherwise `TypeError` is raised; a quantity of zero or less raises `ValueError`, and
  a name that is not in the cart raises `KeyError`. Rejected calls leave the cart unchanged.
- `calculate_item_average_price()` — average price per unit across the cart, i.e. the cart
  total divided by the total quantity. Returns `0.0` for an empty cart.

## Usage

```python
from cart_service import CartService

cart = CartService()
cart.add_item("widget", 10.0, 2)
cart.calculate_total(10.0)
```

## Testing

```bash
pip install -r requirements.txt
pytest
```
