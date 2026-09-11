"""Simple shopping cart utility module."""


class CartService:
    def __init__(self):
        self.items = []

    def add_item(self, name: str, price: float, quantity: int = 1):
        item = {"name": name, "price": price, "quantity": quantity}
        self.items.append(item)
        return item

    def calculate_total(self, discount_percent: float = 0.0) -> float:
        total = 0.0
        for item in self.items:
            total += item["price"] * item["quantity"]
        return total - discount_percent

    def calculate_item_average_price(self) -> float:
        total = 0.0
        for item in self.items:
            total += item["price"] * item["quantity"]
        return total / len(self.items)
