import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from restaurant.models import (
    Category, MenuItem, Customer, Restaurant, Table,
    Order, OrderItem, Reservation, Payment
)


# ====================== BASIC ENTITY TESTS ======================
@pytest.mark.django_db
def test_create_category():
    category = Category.objects.create(name="Burgers")
    assert category.name == "Burgers"


@pytest.mark.django_db
def test_create_menu_item():
    category = Category.objects.create(name="Burgers")

    item = MenuItem.objects.create(
        name="Cheeseburger",
        description="Juicy beef burger",
        price=12.99,
        category=category
    )
    assert item.name == "Cheeseburger"
    assert item.price == 12.99


@pytest.mark.django_db
def test_create_customer():
    user = get_user_model().objects.create_user(
        username="testcustomer",
        password="testpass123",
        email="customer@example.com",
        role=5
    )
    customer = Customer.objects.create(
        user=user,
        phone_number="403-555-9876",
        address="456 Elm Street"
    )
    assert customer.phone_number == "403-555-9876"
    assert customer.address == "456 Elm Street"


@pytest.mark.django_db
def test_create_restaurant():
    restaurant = Restaurant.objects.create(
        name="The Golden Fork",
        address="789 Downtown Ave",
        phone_number="403-555-1111",
        opening_time=timezone.now().time(),
        closing_time=timezone.now().time(),
        latitude=52.27,
        longitude=-113.81
    )
    assert restaurant.name == "The Golden Fork"


# ====================== TABLE & RESERVATION ======================
@pytest.mark.django_db
def test_create_table():
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    table = Table.objects.create(
        label="Table 5",
        seats=4,
        grid_squares={"x": 1, "y": 1},
        status=1,
        restaurant=restaurant
    )
    assert table.label == "Table 5"
    assert table.seats == 4


@pytest.mark.django_db
def test_create_reservation():
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    table = Table.objects.create(label="T1", seats=4, grid_squares={}, status=1, restaurant=restaurant)

    reservation = Reservation.objects.create(
        guest_name="Emma Watson",
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=4,
        status=2,
        deposit_amount=10.00,
        restaurant=restaurant,
        table=table
    )
    assert reservation.guest_name == "Emma Watson"
    assert reservation.party_size == 4


# ====================== ORDER TESTS ======================
@pytest.mark.django_db
def test_create_order_with_items():
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    category = Category.objects.create(name="Burgers")
    menu_item = MenuItem.objects.create(
        name="Cheeseburger", description="Test", price=12.99,
        category=category
    )

    user = get_user_model().objects.create_user(username="testuser", password="pass", role=5)
    customer = Customer.objects.create(user=user, phone_number="123", address="Test")

    order = Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=1,
        sub_total=25.98,
        total_price=25.98,
        order_status=1,
        payment_status=1
    )

    OrderItem.objects.create(
        order=order,
        menu_item=menu_item,
        quantity=2,
        unit_price=12.99
    )

    assert order.orderitem_set.count() == 1
    assert order.total_price == 25.98


@pytest.mark.django_db
def test_order_status_update():
    order = Order.objects.create(
        order_type=1,
        sub_total=20.00,
        total_price=20.00,
        order_status=1,
        payment_status=1
    )
    order.order_status = 4
    order.save()
    assert order.order_status == 4


# ====================== PAYMENT TEST ======================
@pytest.mark.django_db
def test_create_payment():
    order = Order.objects.create(
        order_type=1,
        sub_total=45.50,
        total_price=45.50,
        order_status=1,
        payment_status=1
    )
    
    payment = Payment.objects.create(
        order=order,
        method=1,
        amount=45.50,
        transaction_id="txn_abc12345"
    )
    assert payment.amount == 45.50
    assert payment.transaction_id == "txn_abc12345"


# ====================== EXTRA TESTS ======================
@pytest.mark.django_db
def test_loyalty_points_on_customer():
    user = get_user_model().objects.create_user(username="loyal", password="pass", role=5)
    customer = Customer.objects.create(user=user, phone_number="123", address="Test")
    assert customer.loyalty_points == 0


@pytest.mark.django_db
def test_orderitem_link():
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    category = Category.objects.create(name="Test")
    menu_item = MenuItem.objects.create(
        name="Test Item", description="Test", price=10.0, category=category
    )

    user = get_user_model().objects.create_user(username="test", password="pass", role=5)
    customer = Customer.objects.create(user=user, phone_number="123", address="Test")
    order = Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=1,
        sub_total=20,
        total_price=20,
        order_status=1,
        payment_status=1
    )

    OrderItem.objects.create(order=order, menu_item=menu_item, quantity=2, unit_price=10.0)
    assert order.orderitem_set.count() == 1