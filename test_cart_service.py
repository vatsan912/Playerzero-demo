"""Tests for the CartService shopping cart utility module."""

import pytest

from cart_service import CartService


def test_calculate_total_applies_percentage_discount():
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    assert cart.calculate_total(10.0) == pytest.approx(18.0)


def test_calculate_total_without_discount():
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    cart.add_item("gadget", 5.5)
    assert cart.calculate_total() == pytest.approx(25.5)


def test_calculate_total_full_discount():
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    assert cart.calculate_total(100.0) == pytest.approx(0.0)


def test_calculate_total_empty_cart():
    assert CartService().calculate_total(25.0) == pytest.approx(0.0)


@pytest.mark.parametrize("discount", [-1.0, 100.1, 1000.0])
def test_calculate_total_rejects_out_of_range_discount(discount):
    cart = CartService()
    cart.add_item("widget", 10.0)
    with pytest.raises(ValueError):
        cart.calculate_total(discount)


@pytest.mark.parametrize("discount", ["10", None, True])
def test_calculate_total_rejects_non_numeric_discount(discount):
    cart = CartService()
    cart.add_item("widget", 10.0)
    with pytest.raises(TypeError):
        cart.calculate_total(discount)


def test_average_price_of_empty_cart_is_zero():
    assert CartService().calculate_item_average_price() == pytest.approx(0.0)


def test_average_price_is_weighted_by_quantity():
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    cart.add_item("gadget", 4.0, 2)
    assert cart.calculate_item_average_price() == pytest.approx(7.0)


def test_average_price_single_item_with_quantity():
    cart = CartService()
    cart.add_item("widget", 10.0, 3)
    assert cart.calculate_item_average_price() == pytest.approx(10.0)


@pytest.mark.parametrize("name", ["", "   "])
def test_add_item_rejects_blank_name(name):
    with pytest.raises(ValueError):
        CartService().add_item(name, 10.0)


@pytest.mark.parametrize("name", [None, 5])
def test_add_item_rejects_non_string_name(name):
    with pytest.raises(TypeError):
        CartService().add_item(name, 10.0)


def test_add_item_rejects_negative_price():
    with pytest.raises(ValueError):
        CartService().add_item("widget", -1.0)


@pytest.mark.parametrize("price", ["10.0", None, True])
def test_add_item_rejects_non_numeric_price(price):
    with pytest.raises(TypeError):
        CartService().add_item("widget", price)


@pytest.mark.parametrize("quantity", [0, -3])
def test_add_item_rejects_non_positive_quantity(quantity):
    with pytest.raises(ValueError):
        CartService().add_item("widget", 10.0, quantity)


@pytest.mark.parametrize("quantity", [1.5, "2", None, True])
def test_add_item_rejects_non_integer_quantity(quantity):
    with pytest.raises(TypeError):
        CartService().add_item("widget", 10.0, quantity)


def test_add_item_does_not_store_invalid_input():
    cart = CartService()
    with pytest.raises(ValueError):
        cart.add_item("widget", -1.0)
    assert cart.items == []


def test_add_item_returns_a_copy_of_the_stored_item():
    cart = CartService()
    returned = cart.add_item("widget", 10.0, 2)
    returned["quantity"] = 99
    assert cart.items[0]["quantity"] == 2
    assert cart.calculate_total() == pytest.approx(20.0)


@pytest.mark.parametrize(
    ("coupon_code", "expected_total"),
    [("WELCOME10", 90.0), ("VIP20", 80.0), ("FLASH50", 50.0)],
)
def test_apply_coupon_applies_the_expected_discount(coupon_code, expected_total):
    cart = CartService()
    cart.add_item("widget", 100.0)
    assert cart.apply_coupon(coupon_code) == pytest.approx(expected_total)


@pytest.mark.parametrize("coupon_code", ["vip20", " VIP20 ", "  vip20\n"])
def test_apply_coupon_normalizes_case_and_whitespace(coupon_code):
    cart = CartService()
    cart.add_item("widget", 100.0)
    assert cart.apply_coupon(coupon_code) == pytest.approx(80.0)


def test_apply_coupon_on_empty_cart_returns_zero():
    assert CartService().apply_coupon("FLASH50") == pytest.approx(0.0)


def test_apply_coupon_is_weighted_by_quantity():
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    cart.add_item("gadget", 5.0, 4)
    assert cart.apply_coupon("WELCOME10") == pytest.approx(36.0)


def test_apply_coupon_does_not_mutate_the_cart():
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    cart.apply_coupon("VIP20")
    assert cart.items == [{"name": "widget", "price": 10.0, "quantity": 2}]
    assert cart.calculate_total() == pytest.approx(20.0)


@pytest.mark.parametrize("coupon_code", ["NOPE", "", "   ", "WELCOME 10"])
def test_apply_coupon_rejects_unknown_or_empty_code(coupon_code):
    cart = CartService()
    cart.add_item("widget", 10.0)
    with pytest.raises(ValueError, match="Invalid coupon code"):
        cart.apply_coupon(coupon_code)
    assert cart.items == [{"name": "widget", "price": 10.0, "quantity": 1}]


@pytest.mark.parametrize("coupon_code", [None, 10, ["VIP20"]])
def test_apply_coupon_rejects_non_string_code(coupon_code):
    cart = CartService()
    cart.add_item("widget", 10.0)
    with pytest.raises(TypeError):
        cart.apply_coupon(coupon_code)
    assert cart.items == [{"name": "widget", "price": 10.0, "quantity": 1}]


def test_update_quantity_changes_the_total():
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    cart.update_quantity("widget", 5)
    assert cart.items[0]["quantity"] == 5
    assert cart.calculate_total() == pytest.approx(50.0)


@pytest.mark.parametrize("new_quantity", [1, 3, 10])
def test_update_quantity_accepts_positive_quantities(new_quantity):
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    assert cart.update_quantity("widget", new_quantity)["quantity"] == new_quantity
    assert cart.calculate_total() == pytest.approx(10.0 * new_quantity)


def test_update_quantity_leaves_other_items_untouched():
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    cart.add_item("gadget", 5.0, 3)
    cart.update_quantity("widget", 1)
    assert cart.items[1] == {"name": "gadget", "price": 5.0, "quantity": 3}
    assert cart.calculate_total() == pytest.approx(25.0)


def test_update_quantity_returns_a_copy_of_the_stored_item():
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    returned = cart.update_quantity("widget", 4)
    assert returned == {"name": "widget", "price": 10.0, "quantity": 4}
    returned["quantity"] = 99
    assert cart.items[0]["quantity"] == 4


@pytest.mark.parametrize("new_quantity", [0, -1, -10])
def test_update_quantity_rejects_non_positive_quantity(new_quantity):
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    with pytest.raises(ValueError, match="Quantity must be greater than zero"):
        cart.update_quantity("widget", new_quantity)
    assert cart.items[0]["quantity"] == 2


@pytest.mark.parametrize("new_quantity", [1.5, "2", None, True])
def test_update_quantity_rejects_non_integer_quantity(new_quantity):
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    with pytest.raises(TypeError):
        cart.update_quantity("widget", new_quantity)
    assert cart.items[0]["quantity"] == 2


@pytest.mark.parametrize("item_name", [None, 5, ["widget"]])
def test_update_quantity_rejects_non_string_item_name(item_name):
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    with pytest.raises(TypeError):
        cart.update_quantity(item_name, 3)
    assert cart.items[0]["quantity"] == 2


def test_update_quantity_rejects_unknown_item():
    cart = CartService()
    cart.add_item("widget", 10.0, 2)
    with pytest.raises(KeyError, match="Item not found in cart"):
        cart.update_quantity("gadget", 3)
    assert cart.items == [{"name": "widget", "price": 10.0, "quantity": 2}]


def test_update_quantity_on_empty_cart_rejects_the_item():
    with pytest.raises(KeyError):
        CartService().update_quantity("widget", 1)


def test_update_quantity_is_reflected_in_average_price():
    cart = CartService()
    cart.add_item("widget", 10.0, 1)
    cart.add_item("gadget", 4.0, 1)
    cart.update_quantity("gadget", 3)
    assert cart.calculate_item_average_price() == pytest.approx(5.5)
