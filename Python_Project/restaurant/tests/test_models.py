import pytest 
from django.utils import timezone
from django.contrib.auth import get_user_model
from restaurant.models import (
    Category, MenuItem, Customer, Restaurant, Table,
    Order, OrderItem, Reservation, Payment,
    RestaurantMenuItem, Tag, MenuItemTag, TableLayout # added RestaurantMenuItem, Tag, MenuItemTag, TableLayout as they were missing from Michael's original imports
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


# Verifies SET_NULL behavior on MenuItem when its Category is deleted
@pytest.mark.django_db
def test_menu_item_category_null_on_category_delete():
    # if a category is deleted, menu item should not be deleted
    # category FK on MenuItem uses SET_NULL so item should survive
    category = Category.objects.create(name="Temp Category")
    item = MenuItem.objects.create(
        name="Orphan Item", description="Test", price=5.00, category=category
    )
    category.delete()
    item.refresh_from_db()
    assert item.category is None


# Testin Tag model
@pytest.mark.django_db
def test_create_tag():
    # verifies Tag model saves correctly
    tag = Tag.objects.create(name="Vegan")
    assert tag.name == "Vegan"


# MenuItemTag junction table test 
@pytest.mark.django_db
def test_create_menu_item_tag():
    # verifies MenuItemTag junction table links a MenuItem to a Tag correctly
    category = Category.objects.create(name="Salads")
    item = MenuItem.objects.create(
        name="Caesar Salad", description="Classic", price=9.99, category=category
    )
    tag = Tag.objects.create(name="Contains Nuts")
    menu_item_tag = MenuItemTag.objects.create(menu_item=item, tag=tag)
    assert menu_item_tag.menu_item == item
    assert menu_item_tag.tag == tag


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


# Verifies is_active defaults to True, important for the restaurant activation feature
@pytest.mark.django_db
def test_restaurant_defaults_to_active():
    # is_active defaults to True when a restaurant is created
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    assert restaurant.is_active # checks if is_active is True


# Verifies manager can deactivate a restaurant - required feature in scope doc
@pytest.mark.django_db
def test_restaurant_can_be_deactivated():
    # manager can turn off a restaurant by setting is_active to False
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    restaurant.is_active = False
    restaurant.save()
    restaurant.refresh_from_db()
    assert not restaurant.is_active # checks if is_active is False


# RestaurantMenuItem junction table test
# this is a major ERD change based on professor feedback - one item links to many restaurants
@pytest.mark.django_db
def test_create_restaurant_menu_item():
    # verifies RestaurantMenuItem junction table links a MenuItem to a Restaurant correctly
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    category = Category.objects.create(name="Appetizers")
    item = MenuItem.objects.create(
        name="Garlic Bread", description="Toasted", price=5.00, category=category
    )
    rmi = RestaurantMenuItem.objects.create(
        restaurant=restaurant,
        menu_item=item,
        is_available=True
    )
    assert rmi.is_available # checks if is_available is True
    assert rmi.restaurant == restaurant
    assert rmi.menu_item == item


# Verifies is_available defaults to True on RestaurantMenuItem
@pytest.mark.django_db
def test_restaurant_menu_item_defaults_to_available():
    # is_available on RestaurantMenuItem should default to True
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    category = Category.objects.create(name="Mains")
    item = MenuItem.objects.create(
        name="Steak", description="Grilled", price=25.00, category=category
    )
    rmi = RestaurantMenuItem.objects.create(restaurant=restaurant, menu_item=item)
    assert rmi.is_available # checks if is_available is True


# One MenuItem should link to multiple restaurants without duplicating the record
@pytest.mark.django_db
def test_same_menu_item_linked_to_multiple_restaurants():
    # one MenuItem can be linked to multiple restaurants without duplicating the record
    restaurant1 = Restaurant.objects.create(
        name="Location 1", address="Addr 1", phone_number="111",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    restaurant2 = Restaurant.objects.create(
        name="Location 2", address="Addr 2", phone_number="222",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    category = Category.objects.create(name="Drinks")
    item = MenuItem.objects.create(
        name="Sparkling Water", description="Cold", price=2.50, category=category
    )
    RestaurantMenuItem.objects.create(restaurant=restaurant1, menu_item=item)
    RestaurantMenuItem.objects.create(restaurant=restaurant2, menu_item=item)
    assert RestaurantMenuItem.objects.filter(menu_item=item).count() == 2


# TableLayout model test
@pytest.mark.django_db
def test_create_table_layout():
    # verifies TableLayout saves correctly linked to a restaurant
    user = get_user_model().objects.create_user(username="manager1", password="pass", role=1)
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    layout = TableLayout.objects.create(
        restaurant=restaurant,
        uploaded_by=user,
        grid_data={"grid": []}
    )
    assert layout.restaurant == restaurant
    assert layout.uploaded_by == user


# ====================== TABLE & RESERVATION ======================
# edited: changed status=1 to Table.Status.AVAILABLE - avoids fragile raw integers
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
        status=Table.Status.AVAILABLE,
        restaurant=restaurant
    )
    assert table.label == "Table 5"
    assert table.seats == 4


# Verifies AVAILABLE is the default status for all new tables
@pytest.mark.django_db
def test_table_defaults_to_available():
    # a new table should always start as AVAILABLE
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    table = Table.objects.create(
        label="T1", seats=2, grid_squares={}, restaurant=restaurant
    )
    assert table.status == Table.Status.AVAILABLE


# Verifies server can update table to OCCUPIED - required feature in scope doc
@pytest.mark.django_db
def test_table_status_update_to_occupied():
    # server updates table from AVAILABLE to OCCUPIED
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    table = Table.objects.create(
        label="T2", seats=4, grid_squares={}, restaurant=restaurant
    )
    table.status = Table.Status.OCCUPIED
    table.save()
    table.refresh_from_db()
    assert table.status == Table.Status.OCCUPIED


# Verifies NEEDS_CLEANING status works
# maps to TC-32 in the test plan
@pytest.mark.django_db
def test_table_status_update_to_needs_cleaning():
    # server marks table as NEEDS_CLEANING after guests leave
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    table = Table.objects.create(
        label="T3", seats=4, grid_squares={}, restaurant=restaurant
    )
    table.status = Table.Status.NEEDS_CLEANING
    table.save()
    table.refresh_from_db()
    assert table.status == Table.Status.NEEDS_CLEANING


# edited: changed status=2 to Reservation.Status.CONFIRMED - avoids fragile raw integers
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
        status=Reservation.Status.CONFIRMED,
        deposit_amount=10.00,
        restaurant=restaurant,
        table=table
    )
    assert reservation.guest_name == "Emma Watson"
    assert reservation.party_size == 4


# Verifies PENDING is the default status for all new reservations
@pytest.mark.django_db
def test_reservation_defaults_to_pending():
    # a new reservation should start as PENDING before being confirmed
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    table = Table.objects.create(label="T1", seats=4, grid_squares={}, restaurant=restaurant)
    reservation = Reservation.objects.create(
        guest_name="John Doe",
        reservation_datetime=timezone.now() + timezone.timedelta(hours=2),
        party_size=2,
        deposit_amount=10.00,
        restaurant=restaurant,
        table=table
    )
    assert reservation.status == Reservation.Status.PENDING


# Verifies $10 deposit default - this is a hard business rule agreed with the client
@pytest.mark.django_db
def test_reservation_deposit_defaults_to_ten():
    # deposit should always default to $10 as per client agreement
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    table = Table.objects.create(label="T1", seats=4, grid_squares={}, restaurant=restaurant)
    reservation = Reservation.objects.create(
        guest_name="Jane Doe",
        reservation_datetime=timezone.now() + timezone.timedelta(hours=2),
        party_size=2,
        restaurant=restaurant,
        table=table
    )
    assert reservation.deposit_amount == 10


# Verifies cancellation fee is False by default - fee only applies within 3 hours
@pytest.mark.django_db
def test_reservation_cancellation_fee_defaults_to_false():
    # cancellation fee should not be applied by default
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    table = Table.objects.create(label="T1", seats=4, grid_squares={}, restaurant=restaurant)
    reservation = Reservation.objects.create(
        guest_name="Test Guest",
        reservation_datetime=timezone.now() + timezone.timedelta(hours=5),
        party_size=2,
        deposit_amount=10.00,
        restaurant=restaurant,
        table=table
    )
    assert not reservation.cancellation_fee_applied # checks if cancellation_fee_applied is False


# Verifying $10 fee flag gets set correctly for late cancellations
# maps to TC-19 in the test plan
@pytest.mark.django_db
def test_reservation_cancellation_fee_applied():
    # when a cancellation happens within 3 hours, fee flag should be set to True
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    table = Table.objects.create(label="T1", seats=4, grid_squares={}, restaurant=restaurant)
    reservation = Reservation.objects.create(
        guest_name="Late Cancel",
        reservation_datetime=timezone.now() + timezone.timedelta(hours=1),
        party_size=2,
        deposit_amount=10.00,
        restaurant=restaurant,
        table=table
    )
    reservation.cancellation_fee_applied = True
    reservation.status = Reservation.Status.CANCELLED
    reservation.save()
    reservation.refresh_from_db()
    assert reservation.cancellation_fee_applied # checks if cancellation_fee_applied is True
    assert reservation.status == Reservation.Status.CANCELLED


# Verifies guest reservations work without a Customer record
# maps to TC-31 in the test plan
@pytest.mark.django_db
def test_guest_reservation_no_customer():
    # guests can make reservations without a Customer record
    # customer FK on Reservation is nullable to support this
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    table = Table.objects.create(label="T1", seats=4, grid_squares={}, restaurant=restaurant)
    reservation = Reservation.objects.create(
        guest_name="Walk In Guest",
        guest_email="guest@email.com",
        guest_phone_number="403-000-0000",
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=10.00,
        restaurant=restaurant,
        table=table
    )
    assert reservation.customer is None
    assert reservation.guest_name == "Walk In Guest"


# ====================== ORDER TESTS ======================
# edited: changed all raw integers to Order choice constants throughout order tests
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
        order_type=Order.OrderType.DINE_IN,
        sub_total=25.98,
        total_price=25.98,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )

    OrderItem.objects.create(
        order=order,
        menu_item=menu_item,
        quantity=2,
        unit_price=12.99
    )

    assert order.orderitem_set.count() == 1
    assert order.total_price == 25.98


# edited: changed raw integers to Order choice constants
@pytest.mark.django_db
def test_order_status_update():
    order = Order.objects.create(
        order_type=Order.OrderType.DINE_IN,
        sub_total=20.00,
        total_price=20.00,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    order.order_status = Order.OrderStatus.COMPLETED
    order.save()
    assert order.order_status == Order.OrderStatus.COMPLETED


# Verifies every new order starts as UNPAID
@pytest.mark.django_db
def test_order_defaults_to_unpaid():
    # a new order should always start as UNPAID
    order = Order.objects.create(
        order_type=Order.OrderType.TAKE_OUT,
        sub_total=15.00,
        total_price=15.00,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    assert order.payment_status == Order.PaymentStatus.UNPAID


# Verifies delivery orders store address and fee correctly
@pytest.mark.django_db
def test_delivery_order_has_address():
    # delivery orders must store a delivery address
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    user = get_user_model().objects.create_user(username="deliveryuser", password="pass", role=5)
    customer = Customer.objects.create(user=user, phone_number="123", address="Test")
    order = Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        delivery_address="123 Main St, Toronto, ON",
        delivery_fee=5.00,
        sub_total=20.00,
        total_price=25.00,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    assert order.delivery_address == "123 Main St, Toronto, ON"
    assert order.delivery_fee == 5.00


# Verifies guests can place orders without a Customer record
# customer FK on Order is nullable to support guest ordering
@pytest.mark.django_db
def test_guest_order_no_customer():
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    order = Order.objects.create(
        customer=None,
        restaurant=restaurant,
        order_type=Order.OrderType.TAKE_OUT,
        sub_total=10.00,
        total_price=10.00,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    assert order.customer is None


# Verifies loyalty discount field saves correctly and reflects in total price
@pytest.mark.django_db
def test_order_with_loyalty_discount():
    user = get_user_model().objects.create_user(username="loyaluser", password="pass", role=5)
    customer = Customer.objects.create(user=user, phone_number="123", address="Test")
    order = Order.objects.create(
        customer=customer,
        order_type=Order.OrderType.DINE_IN,
        sub_total=50.00,
        loyalty_discount=10.00,
        total_price=40.00,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    assert order.loyalty_discount == 10.00
    assert order.total_price == 40.00


# Verifies points_earned and points_redeemed save correctly on Order
# Points tracking was moved from PointsLog to Order
@pytest.mark.django_db
def test_order_points_earned_and_redeemed():
    user = get_user_model().objects.create_user(username="pointsuser", password="pass", role=5)
    customer = Customer.objects.create(user=user, phone_number="123", address="Test")
    order = Order.objects.create(
        customer=customer,
        order_type=Order.OrderType.DINE_IN,
        sub_total=30.00,
        total_price=30.00,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID,
        points_earned=300,
        points_redeemed=0
    )
    assert order.points_earned == 300
    assert order.points_redeemed == 0


# ====================== PAYMENT TEST ======================
# edited: changed method=1 to Payment.PaymentMethod.CREDIT_CARD - avoids fragile raw integers
@pytest.mark.django_db
def test_create_payment():
    order = Order.objects.create(
        order_type=Order.OrderType.DINE_IN,
        sub_total=45.50,
        total_price=45.50,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    
    payment = Payment.objects.create(
        order=order,
        method=Payment.PaymentMethod.CREDIT_CARD,
        amount=45.50,
        transaction_id="txn_abc12345"
    )
    assert payment.amount == 45.50
    assert payment.transaction_id == "txn_abc12345"


# Verifies the unique=True constraint on transaction_id enforces no duplicate IDs
@pytest.mark.django_db
def test_payment_transaction_id_is_unique():
    order1 = Order.objects.create(
        order_type=Order.OrderType.DINE_IN,
        sub_total=10.00, total_price=10.00,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    order2 = Order.objects.create(
        order_type=Order.OrderType.TAKE_OUT,
        sub_total=20.00, total_price=20.00,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    Payment.objects.create(
        order=order1, method=Payment.PaymentMethod.CREDIT_CARD,
        amount=10.00, transaction_id="txn_unique_001"
    )
    with pytest.raises(Exception):
        Payment.objects.create(
            order=order2, method=Payment.PaymentMethod.CREDIT_CARD,
            amount=20.00, transaction_id="txn_unique_001"
        )


# ====================== EXTRA TESTS ======================
@pytest.mark.django_db
def test_loyalty_points_on_customer():
    user = get_user_model().objects.create_user(username="loyal", password="pass", role=5)
    customer = Customer.objects.create(user=user, phone_number="123", address="Test")
    assert customer.loyalty_points == 0


# Verifies loyalty_points can be updated on Customer - not just default checked
@pytest.mark.django_db
def test_loyalty_points_update_on_customer():
    user = get_user_model().objects.create_user(username="loyalupdate", password="pass", role=5)
    customer = Customer.objects.create(user=user, phone_number="123", address="Test")
    customer.loyalty_points = 500
    customer.save()
    customer.refresh_from_db()
    assert customer.loyalty_points == 500


# edited: changed raw integers to Order choice constants
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
        order_type=Order.OrderType.DINE_IN,
        sub_total=20,
        total_price=20,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )

    OrderItem.objects.create(order=order, menu_item=menu_item, quantity=2, unit_price=10.0)
    assert order.orderitem_set.count() == 1


# Verifies an order can hold multiple items - extends single item test
@pytest.mark.django_db
def test_multiple_order_items_on_one_order():
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    category = Category.objects.create(name="Test")
    item1 = MenuItem.objects.create(name="Item 1", description="Test", price=10.0, category=category)
    item2 = MenuItem.objects.create(name="Item 2", description="Test", price=15.0, category=category)

    user = get_user_model().objects.create_user(username="multiitem", password="pass", role=5)
    customer = Customer.objects.create(user=user, phone_number="123", address="Test")
    order = Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=Order.OrderType.DINE_IN,
        sub_total=35,
        total_price=35,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )

    OrderItem.objects.create(order=order, menu_item=item1, quantity=1, unit_price=10.0)
    OrderItem.objects.create(order=order, menu_item=item2, quantity=1, unit_price=15.0)
    assert order.orderitem_set.count() == 2


# Verifies assigned_driver and assigned_server link correctly to User
# validates related_name approach on those FKs to avoid reverse accessor conflicts
@pytest.mark.django_db
def test_assigned_driver_and_server_on_order():
    # both use related_name to avoid reverse accessor conflicts on User
    driver = get_user_model().objects.create_user(
        username="driver1", password="pass", role=4
    )
    server = get_user_model().objects.create_user(
        username="server1", password="pass", role=2
    )
    order = Order.objects.create(
        order_type=Order.OrderType.DELIVERY,
        sub_total=20.00,
        total_price=25.00,
        delivery_fee=5.00,
        delivery_address="123 Test St",
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID,
        assigned_driver=driver,
        assigned_server=server
    )
    assert order.assigned_driver == driver
    assert order.assigned_server == server