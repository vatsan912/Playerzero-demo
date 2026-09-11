"""Simple shopping cart utility module."""

from numbers import Real
from typing import Any, Dict, List


class CartService:
    def __init__(self):
        self.items: List[Dict[str, Any]] = []

    def add_item(self, name: str, price: float, quantity: int = 1) -> Dict[str, Any]:
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if not name.strip():
            raise ValueError("name must be a non-empty string")
        if isinstance(price, bool) or not isinstance(price, Real):
            raise TypeError("price must be a real number")
        if price < 0:
            raise ValueError("price must not be negative")
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise TypeError("quantity must be an integer")
        if quantity < 1:
            raise ValueError("quantity must be a positive integer")
        item = {"name": name, "price": float(price), "quantity": quantity}
        self.items.append(item)
        return dict(item)

    def calculate_total(self, discount_percent: float = 0.0) -> float:
        if isinstance(discount_percent, bool) or not isinstance(discount_percent, Real):
            raise TypeError("discount_percent must be a real number")
        if not 0.0 <= float(discount_percent) <= 100.0:
            raise ValueError("discount_percent must be between 0 and 100")
        return self._subtotal() * (1.0 - float(discount_percent) / 100.0)

    def calculate_item_average_price(self) -> float:
        total_quantity = sum(item["quantity"] for item in self.items)
        if total_quantity <= 0:
            return 0.0
        return self._subtotal() / total_quantity

    def _subtotal(self) -> float:
        total = 0.0
        for item in self.items:
            total += item["price"] * item["quantity"]
        return total
