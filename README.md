# Cart Service

A standalone Python utility module that provides `CartService`, a minimal shopping cart
that tracks items (name, price, quantity) and computes order totals.

## API

- `add_item(name, price, quantity=1)` — add an item to the cart. `name` must be a non-empty
  string, `price` a non-negative number, and `quantity` a positive integer; invalid input
  raises `TypeError` or `ValueError` and nothing is added to the cart.
- `calculate_total(discount_percent=0.0)` — total price of the cart after applying a
  percentage discount. `discount_percent` must be a number between 0 and 100.
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
