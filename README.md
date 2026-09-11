# Cart Service

A standalone Python utility module that provides `CartService`, a minimal shopping cart
that tracks items (name, price, quantity) and computes order totals.

## API

- `add_item(name, price, quantity=1)` — add an item to the cart.
- `calculate_total(discount_percent=0.0)` — total price of the cart after applying a
  percentage discount.
- `calculate_item_average_price()` — average price across the items in the cart.

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
