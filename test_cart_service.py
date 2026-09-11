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
