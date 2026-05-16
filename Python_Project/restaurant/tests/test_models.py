import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
import datetime
from restaurant.models import (
    Category, MenuItem, Customer, Restaurant, Table,
    Order, OrderItem, Reservation, Payment,
    RestaurantMenuItem, Tag, MenuItemTag, TableLayout,
    Notification, PreOrder, PreOrderItem,
    TableTransferRequest, ManagerNote, Inventory,
    StaffInvite
)

User = get_user_model()


# ====================== HELPER FACTORIES ======================
# small helper functions to avoid repeating object creation boilerplate across tests
# each helper creates the minimum required fields to produce a valid object

def make_restaurant(name='Test Restaurant'):
    # creates a valid restaurant with realistic Calgary coordinates
    return Restaurant.objects.create(
        name=name,
        address='123 Test St, Calgary, AB',
        phone_number='403-555-1234',
        opening_time=datetime.time(9, 0),
        closing_time=datetime.time(22, 0),
        latitude=Decimal('51.044733'),
        longitude=Decimal('-114.071883'),
        is_active=True
    )


def make_user(username='testuser', role=5):
    # creates a user with the given role, defaults to CUSTOMER
    return User.objects.create_user(
        username=username,
        password='TestPass123!',
        email=f'{username}@test.com',
        role=role
    )


def make_customer(username='testcustomer', loyalty_points=0):
    # creates a customer user and their linked customer profile
    user = make_user(username=username, role=User.Role.CUSTOMER)
    return Customer.objects.create(
        user=user,
        phone_number='4031234567',
        address='100 Test Ave',
        loyalty_points=loyalty_points
    )


def make_table(restaurant, label='T1', seats=4, status=None):
    # creates a table linked to the given restaurant
    return Table.objects.create(
        label=label,
        seats=seats,
        grid_squares={'x': 1, 'y': 1, 'w': 1, 'h': 1},
        status=status or Table.Status.AVAILABLE,
        restaurant=restaurant
    )


def make_menu_item(name='Test Burger', price='12.99', category=None):
    # creates a menu item, creating a default category if none is provided
    if category is None:
        category = Category.objects.create(name='Test Category')
    return MenuItem.objects.create(
        name=name,
        description='A test item',
        price=Decimal(price),
        category=category
    )


def make_order(restaurant=None, customer=None, order_type=None, status=None, payment_status=None):
    # creates a minimal valid order with sensible defaults
    return Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=order_type or Order.OrderType.DINE_IN,
        sub_total=Decimal('20.00'),
        tax_amount=Decimal('1.00'),
        total_price=Decimal('21.00'),
        order_status=status or Order.OrderStatus.PENDING,
        payment_status=payment_status or Order.PaymentStatus.UNPAID
    )


# ====================== CATEGORY TESTS ======================

@pytest.mark.django_db
def test_create_category():
    # verifies a category can be created and its name saved correctly
    category = Category.objects.create(name='Burgers')
    assert category.name == 'Burgers'


@pytest.mark.django_db
def test_category_str_returns_name():
    # verifies the string representation of a category is its name
    category = Category.objects.create(name='Desserts')
    assert str(category) == 'Desserts'


@pytest.mark.django_db
def test_category_auto_timestamps():
    # verifies created_at is set automatically on category creation
    category = Category.objects.create(name='Drinks')
    assert category.created_at is not None


@pytest.mark.django_db
def test_multiple_categories_are_independent():
    # verifies multiple categories can coexist without conflict
    Category.objects.create(name='Burgers')
    Category.objects.create(name='Sides')
    assert Category.objects.count() == 2


# ====================== TAG TESTS ======================

@pytest.mark.django_db
def test_create_tag():
    # verifies a tag can be created and its name saved correctly
    tag = Tag.objects.create(name='Vegan')
    assert tag.name == 'Vegan'


@pytest.mark.django_db
def test_tag_str_returns_name():
    # verifies the string representation of a tag is its name
    tag = Tag.objects.create(name='Spicy')
    assert str(tag) == 'Spicy'


@pytest.mark.django_db
def test_menu_item_tag_junction():
    # verifies MenuItemTag junction table links a MenuItem to a Tag correctly
    category = Category.objects.create(name='Salads')
    item = MenuItem.objects.create(
        name='Caesar Salad', description='Classic', price=Decimal('9.99'), category=category
    )
    tag = Tag.objects.create(name='Contains Nuts')
    menu_item_tag = MenuItemTag.objects.create(menu_item=item, tag=tag)
    assert menu_item_tag.menu_item == item
    assert menu_item_tag.tag == tag


@pytest.mark.django_db
def test_menu_item_can_have_multiple_tags():
    # verifies one menu item can be linked to multiple tags
    category = Category.objects.create(name='Test')
    item = make_menu_item(category=category)
    tag1 = Tag.objects.create(name='Vegan')
    tag2 = Tag.objects.create(name='Gluten Free')
    MenuItemTag.objects.create(menu_item=item, tag=tag1)
    MenuItemTag.objects.create(menu_item=item, tag=tag2)
    assert MenuItemTag.objects.filter(menu_item=item).count() == 2


# ====================== MENU ITEM TESTS ======================

@pytest.mark.django_db
def test_create_menu_item():
    # verifies a menu item can be created with all required fields
    category = Category.objects.create(name='Burgers')
    item = MenuItem.objects.create(
        name='Cheeseburger',
        description='Juicy beef burger',
        price=Decimal('12.99'),
        category=category
    )
    assert item.name == 'Cheeseburger'
    assert item.price == Decimal('12.99')


@pytest.mark.django_db
def test_menu_item_str_returns_name():
    # verifies the string representation of a menu item is its name
    item = make_menu_item(name='Test Steak')
    assert str(item) == 'Test Steak'


@pytest.mark.django_db
def test_menu_item_category_null_on_category_delete():
    # verifies SET_NULL behavior: if a category is deleted the menu item survives
    # the category FK on MenuItem uses SET_NULL so the item is not deleted
    category = Category.objects.create(name='Temp Category')
    item = MenuItem.objects.create(
        name='Orphan Item', description='Test', price=Decimal('5.00'), category=category
    )
    category.delete()
    item.refresh_from_db()
    assert item.category is None


@pytest.mark.django_db
def test_menu_item_without_image_is_valid():
    # verifies menu items do not require an image (image field is nullable)
    item = make_menu_item()
    assert item.image.name is None or item.image.name == ''


# ====================== RESTAURANT MENU ITEM TESTS ======================

@pytest.mark.django_db
def test_create_restaurant_menu_item():
    # verifies RestaurantMenuItem junction table links a MenuItem to a Restaurant correctly
    restaurant = make_restaurant()
    item = make_menu_item()
    rmi = RestaurantMenuItem.objects.create(
        restaurant=restaurant, menu_item=item, is_available=True
    )
    assert rmi.is_available is True
    assert rmi.restaurant == restaurant
    assert rmi.menu_item == item


@pytest.mark.django_db
def test_restaurant_menu_item_defaults_to_available():
    # verifies is_available defaults to True when not explicitly set
    restaurant = make_restaurant()
    item = make_menu_item()
    rmi = RestaurantMenuItem.objects.create(restaurant=restaurant, menu_item=item)
    assert rmi.is_available is True


@pytest.mark.django_db
def test_same_menu_item_linked_to_multiple_restaurants():
    # verifies one MenuItem can be linked to multiple restaurants without duplicating the item
    restaurant1 = make_restaurant(name='Location 1')
    restaurant2 = make_restaurant(name='Location 2')
    item = make_menu_item()
    RestaurantMenuItem.objects.create(restaurant=restaurant1, menu_item=item)
    RestaurantMenuItem.objects.create(restaurant=restaurant2, menu_item=item)
    assert RestaurantMenuItem.objects.filter(menu_item=item).count() == 2


@pytest.mark.django_db
def test_marking_item_unavailable_saves_correctly():
    # verifies toggling is_available to False saves and persists correctly
    restaurant = make_restaurant()
    item = make_menu_item()
    rmi = RestaurantMenuItem.objects.create(restaurant=restaurant, menu_item=item, is_available=True)
    rmi.is_available = False
    rmi.save()
    rmi.refresh_from_db()
    assert rmi.is_available is False


@pytest.mark.django_db
def test_marking_item_available_again_saves_correctly():
    # verifies toggling is_available back to True after setting to False works correctly
    restaurant = make_restaurant()
    item = make_menu_item()
    rmi = RestaurantMenuItem.objects.create(restaurant=restaurant, menu_item=item, is_available=False)
    rmi.is_available = True
    rmi.save()
    rmi.refresh_from_db()
    assert rmi.is_available is True


# ====================== CUSTOMER TESTS ======================

@pytest.mark.django_db
def test_create_customer():
    # verifies a customer profile can be created linked to a user
    user = make_user(username='testcustomer', role=User.Role.CUSTOMER)
    customer = Customer.objects.create(
        user=user,
        phone_number='403-555-9876',
        address='456 Elm Street',
        loyalty_points=0
    )
    assert customer.phone_number == '403-555-9876'
    assert customer.address == '456 Elm Street'


@pytest.mark.django_db
def test_customer_loyalty_points_default_to_zero():
    # verifies a new customer always starts with 0 loyalty points
    customer = make_customer(username='loyaldefault')
    assert customer.loyalty_points == 0


@pytest.mark.django_db
def test_loyalty_points_can_be_updated():
    # verifies loyalty points can be incremented and saved correctly
    customer = make_customer(username='loyalupdate')
    customer.loyalty_points = 500
    customer.save()
    customer.refresh_from_db()
    assert customer.loyalty_points == 500


@pytest.mark.django_db
def test_loyalty_points_can_be_decremented():
    # verifies loyalty points can be decremented for redemption
    customer = make_customer(username='loyalredeem', loyalty_points=1000)
    customer.loyalty_points -= 1000
    customer.save()
    customer.refresh_from_db()
    assert customer.loyalty_points == 0


@pytest.mark.django_db
def test_customer_str_returns_full_name():
    # verifies the string representation of a customer is first and last name
    user = make_user(username='fullname', role=User.Role.CUSTOMER)
    user.first_name = 'Clark'
    user.last_name = 'Kent'
    user.save()
    customer = Customer.objects.create(
        user=user, phone_number='4031234567', address='123 Test St'
    )
    assert str(customer) == 'Clark Kent'


@pytest.mark.django_db
def test_deleting_user_cascades_to_customer():
    # verifies that deleting the User record also deletes the linked Customer
    # Customer uses CASCADE on the User FK so this should always happen
    customer = make_customer(username='cascadetest')
    user_pk = customer.user.pk
    customer.user.delete()
    assert not Customer.objects.filter(pk=customer.pk).exists()


# ====================== RESTAURANT TESTS ======================

@pytest.mark.django_db
def test_create_restaurant():
    # verifies a restaurant can be created with all required fields
    restaurant = make_restaurant(name='The Golden Fork')
    assert restaurant.name == 'The Golden Fork'
    assert restaurant.is_active is True


@pytest.mark.django_db
def test_restaurant_str_returns_name():
    # verifies the string representation of a restaurant is its name
    restaurant = make_restaurant(name='Urban Spark')
    assert str(restaurant) == 'Urban Spark'


@pytest.mark.django_db
def test_restaurant_defaults_to_active():
    # verifies is_active defaults to True when a new restaurant is created
    restaurant = make_restaurant()
    assert restaurant.is_active is True


@pytest.mark.django_db
def test_restaurant_can_be_deactivated():
    # verifies a restaurant can be deactivated by setting is_active to False
    restaurant = make_restaurant()
    restaurant.is_active = False
    restaurant.save()
    restaurant.refresh_from_db()
    assert restaurant.is_active is False


@pytest.mark.django_db
def test_restaurant_closing_time_before_opening_raises_validation_error():
    # verifies the clean() method rejects closing times before opening times
    restaurant = Restaurant(
        name='Bad Hours',
        address='Test',
        phone_number='123',
        opening_time=datetime.time(22, 0),
        closing_time=datetime.time(9, 0),
        latitude=Decimal('51.0'),
        longitude=Decimal('-114.0')
    )
    with pytest.raises(ValidationError):
        restaurant.clean()


@pytest.mark.django_db
def test_restaurant_user_fk_is_nullable():
    # verifies the user FK on Restaurant is SET_NULL so restaurant survives if manager is deleted
    manager = make_user(username='deletablemanager', role=User.Role.MANAGER)
    restaurant = Restaurant.objects.create(
        name='Test',
        address='Addr',
        phone_number='123',
        opening_time=datetime.time(9, 0),
        closing_time=datetime.time(22, 0),
        latitude=Decimal('51.0'),
        longitude=Decimal('-114.0'),
        user=manager
    )
    manager.delete()
    restaurant.refresh_from_db()
    assert restaurant.user is None


# ====================== TABLE TESTS ======================

@pytest.mark.django_db
def test_create_table():
    # verifies a table can be created with all required fields
    restaurant = make_restaurant()
    table = make_table(restaurant, label='T1', seats=4)
    assert table.label == 'T1'
    assert table.seats == 4


@pytest.mark.django_db
def test_table_defaults_to_available():
    # verifies a new table always starts with AVAILABLE status
    restaurant = make_restaurant()
    table = Table.objects.create(
        label='T1', seats=2, grid_squares={}, restaurant=restaurant
    )
    assert table.status == Table.Status.AVAILABLE


@pytest.mark.django_db
def test_table_status_update_to_occupied():
    # verifies a table status can be changed to OCCUPIED
    restaurant = make_restaurant()
    table = make_table(restaurant)
    table.status = Table.Status.OCCUPIED
    table.save()
    table.refresh_from_db()
    assert table.status == Table.Status.OCCUPIED


@pytest.mark.django_db
def test_table_status_update_to_needs_cleaning():
    # verifies a table status can be changed to NEEDS_CLEANING after guests leave
    restaurant = make_restaurant()
    table = make_table(restaurant)
    table.status = Table.Status.NEEDS_CLEANING
    table.save()
    table.refresh_from_db()
    assert table.status == Table.Status.NEEDS_CLEANING


@pytest.mark.django_db
def test_table_status_update_to_reserved():
    # verifies a table status can be changed to RESERVED when a reservation is created
    restaurant = make_restaurant()
    table = make_table(restaurant)
    table.status = Table.Status.RESERVED
    table.save()
    table.refresh_from_db()
    assert table.status == Table.Status.RESERVED


@pytest.mark.django_db
def test_table_assigned_server_can_be_set():
    # verifies a server can be assigned to a table via the assigned_server FK
    restaurant = make_restaurant()
    server = make_user(username='assignserver', role=User.Role.SERVER_HOST)
    table = make_table(restaurant)
    table.assigned_server = server
    table.save()
    table.refresh_from_db()
    assert table.assigned_server == server


@pytest.mark.django_db
def test_table_assigned_server_set_null_on_user_delete():
    # verifies the assigned_server FK uses SET_NULL so table survives if server is deleted
    restaurant = make_restaurant()
    server = make_user(username='deletableserver', role=User.Role.SERVER_HOST)
    table = make_table(restaurant)
    table.assigned_server = server
    table.save()
    server.delete()
    table.refresh_from_db()
    assert table.assigned_server is None


@pytest.mark.django_db
def test_table_str_includes_label_and_restaurant():
    # verifies the string representation includes both the table label and restaurant name
    restaurant = make_restaurant(name='Test Restaurant')
    table = make_table(restaurant, label='T1')
    assert 'T1' in str(table)
    assert 'Test Restaurant' in str(table)


@pytest.mark.django_db
def test_deleting_restaurant_cascades_to_tables():
    # verifies that deleting a restaurant also deletes all its tables
    restaurant = make_restaurant()
    make_table(restaurant, label='T1')
    make_table(restaurant, label='T2')
    restaurant.delete()
    assert Table.objects.filter(label__in=['T1', 'T2']).count() == 0


# ====================== TABLE LAYOUT TESTS ======================

@pytest.mark.django_db
def test_create_table_layout():
    # verifies a TableLayout can be saved correctly linked to a restaurant
    manager = make_user(username='layoutmanager', role=User.Role.MANAGER)
    restaurant = make_restaurant()
    layout = TableLayout.objects.create(
        restaurant=restaurant,
        uploaded_by=manager,
        grid_data={'grid': []}
    )
    assert layout.restaurant == restaurant
    assert layout.uploaded_by == manager


@pytest.mark.django_db
def test_table_layout_grid_data_saves_as_json():
    # verifies complex grid_data with table positions saves and retrieves correctly
    manager = make_user(username='gridmanager', role=User.Role.MANAGER)
    restaurant = make_restaurant()
    grid = [
        {'table_id': 1, 'label': 'T1', 'x': 2, 'y': 3, 'w': 1, 'h': 1},
        {'table_id': 2, 'label': 'T2', 'x': 4, 'y': 3, 'w': 2, 'h': 1},
    ]
    layout = TableLayout.objects.create(
        restaurant=restaurant, uploaded_by=manager, grid_data=grid
    )
    layout.refresh_from_db()
    assert layout.grid_data[0]['label'] == 'T1'
    assert layout.grid_data[1]['x'] == 4


# ====================== RESERVATION TESTS ======================

@pytest.mark.django_db
def test_create_reservation():
    # verifies a reservation can be created with all required fields
    restaurant = make_restaurant()
    table = make_table(restaurant)
    reservation = Reservation.objects.create(
        guest_name='Emma Watson',
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=4,
        status=Reservation.Status.CONFIRMED,
        deposit_amount=Decimal('10.00'),
        restaurant=restaurant,
        table=table
    )
    assert reservation.guest_name == 'Emma Watson'
    assert reservation.party_size == 4


@pytest.mark.django_db
def test_reservation_defaults_to_pending():
    # verifies a new reservation always starts with PENDING status
    restaurant = make_restaurant()
    table = make_table(restaurant)
    reservation = Reservation.objects.create(
        guest_name='John Doe',
        reservation_datetime=timezone.now() + timezone.timedelta(hours=2),
        party_size=2,
        deposit_amount=Decimal('10.00'),
        restaurant=restaurant,
        table=table
    )
    assert reservation.status == Reservation.Status.PENDING


@pytest.mark.django_db
def test_reservation_deposit_defaults_to_ten():
    # verifies the deposit always defaults to $10 as per the business rule
    restaurant = make_restaurant()
    table = make_table(restaurant)
    reservation = Reservation.objects.create(
        guest_name='Jane Doe',
        reservation_datetime=timezone.now() + timezone.timedelta(hours=2),
        party_size=2,
        restaurant=restaurant,
        table=table
    )
    assert reservation.deposit_amount == Decimal('10.00')


@pytest.mark.django_db
def test_reservation_cancellation_fee_defaults_to_false():
    # verifies the cancellation fee flag is False by default
    restaurant = make_restaurant()
    table = make_table(restaurant)
    reservation = Reservation.objects.create(
        guest_name='Test Guest',
        reservation_datetime=timezone.now() + timezone.timedelta(hours=5),
        party_size=2,
        deposit_amount=Decimal('10.00'),
        restaurant=restaurant,
        table=table
    )
    assert reservation.cancellation_fee_applied is False


@pytest.mark.django_db
def test_reservation_cancellation_fee_applied_on_late_cancel():
    # verifies the cancellation fee flag can be set when cancelling within 3 hours
    restaurant = make_restaurant()
    table = make_table(restaurant)
    reservation = Reservation.objects.create(
        guest_name='Late Cancel',
        reservation_datetime=timezone.now() + timezone.timedelta(hours=1),
        party_size=2,
        deposit_amount=Decimal('10.00'),
        restaurant=restaurant,
        table=table
    )
    reservation.cancellation_fee_applied = True
    reservation.status = Reservation.Status.CANCELLED
    reservation.save()
    reservation.refresh_from_db()
    assert reservation.cancellation_fee_applied is True
    assert reservation.status == Reservation.Status.CANCELLED


@pytest.mark.django_db
def test_guest_reservation_without_customer_account():
    # verifies guests can make reservations without a Customer record
    # the customer FK on Reservation is nullable to support walk-in guests
    restaurant = make_restaurant()
    table = make_table(restaurant)
    reservation = Reservation.objects.create(
        guest_name='Walk In Guest',
        guest_email='guest@email.com',
        guest_phone_number='403-000-0000',
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=Decimal('10.00'),
        restaurant=restaurant,
        table=table
    )
    assert reservation.customer is None
    assert reservation.guest_name == 'Walk In Guest'


@pytest.mark.django_db
def test_reservation_party_size_zero_raises_validation_error():
    # verifies the clean() method rejects party sizes of zero or less
    restaurant = make_restaurant()
    table = make_table(restaurant)
    reservation = Reservation(
        guest_name='Test',
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=0,
        deposit_amount=Decimal('10.00'),
        restaurant=restaurant,
        table=table
    )
    with pytest.raises(ValidationError):
        reservation.clean()


@pytest.mark.django_db
def test_reservation_str_includes_id_and_restaurant():
    # verifies the string representation includes the reservation id and restaurant name
    restaurant = make_restaurant(name='Urban Spark')
    table = make_table(restaurant)
    reservation = Reservation.objects.create(
        guest_name='Test',
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=Decimal('10.00'),
        restaurant=restaurant,
        table=table
    )
    assert 'Urban Spark' in str(reservation)


# ====================== ORDER TESTS ======================

@pytest.mark.django_db
def test_create_order_with_items():
    # verifies an order can be created with linked order items
    restaurant = make_restaurant()
    customer = make_customer(username='ordertest')
    item = make_menu_item()
    order = make_order(restaurant=restaurant, customer=customer)
    OrderItem.objects.create(order=order, menu_item=item, quantity=2, unit_price=Decimal('12.99'))
    assert order.orderitem_set.count() == 1
    assert order.total_price == Decimal('21.00')


@pytest.mark.django_db
def test_order_status_can_be_updated():
    # verifies order status can be advanced through the workflow
    order = make_order()
    order.order_status = Order.OrderStatus.COMPLETED
    order.save()
    assert order.order_status == Order.OrderStatus.COMPLETED


@pytest.mark.django_db
def test_order_defaults_to_unpaid():
    # verifies a new order always starts as UNPAID
    order = make_order()
    assert order.payment_status == Order.PaymentStatus.UNPAID


@pytest.mark.django_db
def test_order_defaults_to_pending():
    # verifies a new order always starts as PENDING
    order = make_order()
    assert order.order_status == Order.OrderStatus.PENDING


@pytest.mark.django_db
def test_delivery_order_has_address_and_fee():
    # verifies delivery orders store a delivery address and fee correctly
    restaurant = make_restaurant()
    customer = make_customer(username='deliverytest')
    order = Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        delivery_address='123 Main St, Calgary, AB',
        delivery_fee=Decimal('5.00'),
        sub_total=Decimal('20.00'),
        tax_amount=Decimal('1.00'),
        total_price=Decimal('26.00'),
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    assert order.delivery_address == '123 Main St, Calgary, AB'
    assert order.delivery_fee == Decimal('5.00')


@pytest.mark.django_db
def test_guest_order_has_no_customer():
    # verifies guest orders can be created without a Customer record
    # the customer FK on Order is nullable to support this
    restaurant = make_restaurant()
    order = Order.objects.create(
        customer=None,
        restaurant=restaurant,
        order_type=Order.OrderType.TAKE_OUT,
        sub_total=Decimal('10.00'),
        total_price=Decimal('10.00'),
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    assert order.customer is None


@pytest.mark.django_db
def test_order_with_loyalty_discount():
    # verifies loyalty discount field saves and reflects in the total correctly
    customer = make_customer(username='loyaldiscount')
    order = Order.objects.create(
        customer=customer,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('50.00'),
        loyalty_discount=Decimal('10.00'),
        tax_amount=Decimal('2.00'),
        total_price=Decimal('42.00'),
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    assert order.loyalty_discount == Decimal('10.00')
    assert order.total_price == Decimal('42.00')


@pytest.mark.django_db
def test_order_points_earned_and_redeemed():
    # verifies points_earned and points_redeemed save correctly on the order
    customer = make_customer(username='pointstest')
    order = Order.objects.create(
        customer=customer,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('30.00'),
        total_price=Decimal('30.00'),
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID,
        points_earned=300,
        points_redeemed=0
    )
    assert order.points_earned == 300
    assert order.points_redeemed == 0


@pytest.mark.django_db
def test_multiple_order_items_on_one_order():
    # verifies an order can hold multiple items from different menu items
    restaurant = make_restaurant()
    customer = make_customer(username='multiitem')
    category = Category.objects.create(name='Test')
    item1 = make_menu_item(name='Item 1', category=category)
    item2 = make_menu_item(name='Item 2', category=category)
    order = make_order(restaurant=restaurant, customer=customer)
    OrderItem.objects.create(order=order, menu_item=item1, quantity=1, unit_price=Decimal('10.00'))
    OrderItem.objects.create(order=order, menu_item=item2, quantity=1, unit_price=Decimal('15.00'))
    assert order.orderitem_set.count() == 2


@pytest.mark.django_db
def test_assigned_driver_and_server_on_order():
    # verifies both assigned_driver and assigned_server FKs save correctly on an order
    # uses related_name approach on the User FK to avoid reverse accessor conflicts
    driver = make_user(username='testdriver', role=User.Role.DELIVERY_DRIVER)
    server = make_user(username='testserver', role=User.Role.SERVER_HOST)
    order = Order.objects.create(
        order_type=Order.OrderType.DELIVERY,
        sub_total=Decimal('20.00'),
        total_price=Decimal('25.00'),
        delivery_fee=Decimal('5.00'),
        delivery_address='123 Test St',
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID,
        assigned_driver=driver,
        assigned_server=server
    )
    assert order.assigned_driver == driver
    assert order.assigned_server == server


@pytest.mark.django_db
def test_order_table_fk_links_correctly():
    # verifies the table FK on Order links to the correct table object
    restaurant = make_restaurant()
    table = make_table(restaurant, label='T1')
    order = make_order(restaurant=restaurant)
    order.table = table
    order.save()
    order.refresh_from_db()
    assert order.table == table


@pytest.mark.django_db
def test_order_tax_amount_saves_correctly():
    # verifies the tax_amount field saves and retrieves correctly
    order = Order.objects.create(
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('20.00'),
        tax_amount=Decimal('1.00'),
        total_price=Decimal('21.00'),
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    assert order.tax_amount == Decimal('1.00')


@pytest.mark.django_db
def test_deleting_order_cascades_to_order_items():
    # verifies that deleting an order also deletes all its linked order items
    restaurant = make_restaurant()
    customer = make_customer(username='cascadeorder')
    item = make_menu_item()
    order = make_order(restaurant=restaurant, customer=customer)
    OrderItem.objects.create(order=order, menu_item=item, quantity=1, unit_price=Decimal('12.99'))
    order.delete()
    assert OrderItem.objects.count() == 0


# ====================== PAYMENT TESTS ======================

@pytest.mark.django_db
def test_create_payment():
    # verifies a payment record can be created and linked to an order
    order = make_order()
    payment = Payment.objects.create(
        order=order,
        method=Payment.PaymentMethod.CREDIT_CARD,
        amount=Decimal('45.50'),
        transaction_id='txn_abc12345',
        status='succeeded'
    )
    assert payment.amount == Decimal('45.50')
    assert payment.transaction_id == 'txn_abc12345'
    assert payment.status == 'succeeded'


@pytest.mark.django_db
def test_payment_transaction_id_is_unique():
    # verifies the unique constraint on transaction_id prevents duplicate payment records
    order1 = make_order()
    order2 = make_order()
    Payment.objects.create(
        order=order1, method=Payment.PaymentMethod.CREDIT_CARD,
        amount=Decimal('10.00'), transaction_id='txn_unique_001'
    )
    with pytest.raises(Exception):
        Payment.objects.create(
            order=order2, method=Payment.PaymentMethod.CREDIT_CARD,
            amount=Decimal('20.00'), transaction_id='txn_unique_001'
        )


@pytest.mark.django_db
def test_failed_payment_status_saves_correctly():
    # verifies a failed payment record can be saved with status=failed
    order = make_order()
    payment = Payment.objects.create(
        order=order,
        method=Payment.PaymentMethod.CREDIT_CARD,
        amount=Decimal('20.00'),
        transaction_id='txn_failed_001',
        status='failed'
    )
    assert payment.status == 'failed'


@pytest.mark.django_db
def test_multiple_payments_can_link_to_same_order():
    # verifies multiple payment attempts can exist for the same order (retry scenario)
    # each has a different transaction_id since the unique constraint is per transaction
    order = make_order()
    Payment.objects.create(
        order=order, method=Payment.PaymentMethod.CREDIT_CARD,
        amount=Decimal('20.00'), transaction_id='txn_attempt_1', status='failed'
    )
    Payment.objects.create(
        order=order, method=Payment.PaymentMethod.CREDIT_CARD,
        amount=Decimal('20.00'), transaction_id='txn_attempt_2', status='succeeded'
    )
    assert Payment.objects.filter(order=order).count() == 2


# ====================== INVENTORY TESTS ======================

@pytest.mark.django_db
def test_create_inventory_item():
    # verifies an inventory item can be created linked to a restaurant
    restaurant = make_restaurant()
    item = Inventory.objects.create(
        restaurant=restaurant,
        ingredient_name='Beef Patties',
        current_level=Decimal('50.00'),
        unit='kg',
        reorder_level=Decimal('10.00')
    )
    assert item.ingredient_name == 'Beef Patties'
    assert item.current_level == Decimal('50.00')


@pytest.mark.django_db
def test_inventory_low_stock_detection():
    # verifies an inventory item is correctly identified as low stock
    # low stock means current_level is at or below reorder_level
    restaurant = make_restaurant()
    item = Inventory.objects.create(
        restaurant=restaurant,
        ingredient_name='Burger Buns',
        current_level=Decimal('5.00'),
        unit='units',
        reorder_level=Decimal('20.00')
    )
    assert item.current_level <= item.reorder_level


@pytest.mark.django_db
def test_inventory_healthy_stock_detection():
    # verifies an inventory item with current level above reorder is not flagged as low stock
    restaurant = make_restaurant()
    item = Inventory.objects.create(
        restaurant=restaurant,
        ingredient_name='Potatoes',
        current_level=Decimal('80.00'),
        unit='kg',
        reorder_level=Decimal('15.00')
    )
    assert item.current_level > item.reorder_level


@pytest.mark.django_db
def test_inventory_deleted_when_restaurant_deleted():
    # verifies inventory records are deleted when their restaurant is deleted (CASCADE)
    restaurant = make_restaurant()
    Inventory.objects.create(
        restaurant=restaurant,
        ingredient_name='Test Item',
        current_level=Decimal('10.00'),
        unit='kg',
        reorder_level=Decimal('5.00')
    )
    restaurant.delete()
    assert Inventory.objects.filter(ingredient_name='Test Item').count() == 0


# ====================== STAFF INVITE TESTS ======================

@pytest.mark.django_db
def test_create_staff_invite():
    # verifies a staff invite can be created for a given email and role
    invite = StaffInvite.objects.create(
        email='newstaff@test.com',
        role=User.Role.SERVER_HOST
    )
    assert invite.email == 'newstaff@test.com'
    assert invite.is_used is False


@pytest.mark.django_db
def test_staff_invite_defaults_to_unused():
    # verifies a new invite always starts with is_used set to False
    invite = StaffInvite.objects.create(
        email='unused@test.com', role=User.Role.KITCHEN_STAFF
    )
    assert invite.is_used is False


@pytest.mark.django_db
def test_staff_invite_can_be_marked_as_used():
    # verifies is_used can be set to True after the staff member registers
    invite = StaffInvite.objects.create(
        email='used@test.com', role=User.Role.DELIVERY_DRIVER
    )
    invite.is_used = True
    invite.save()
    invite.refresh_from_db()
    assert invite.is_used is True


# ====================== NOTIFICATION TESTS ======================

@pytest.mark.django_db
def test_create_order_ready_notification():
    # verifies an ORDER_READY notification can be created and saved correctly
    restaurant = make_restaurant()
    table = make_table(restaurant)
    order = make_order(restaurant=restaurant)
    notification = Notification.objects.create(
        table=table,
        order=order,
        notification_type=Notification.NotificationType.ORDER_READY,
        message=f'Order #{order.id} is ready!',
        is_read=False
    )
    assert notification.is_read is False
    assert notification.notification_type == Notification.NotificationType.ORDER_READY


@pytest.mark.django_db
def test_create_table_attention_notification():
    # verifies a TABLE_ATTENTION notification can be created for host mode requests
    restaurant = make_restaurant()
    table = make_table(restaurant)
    order = make_order(restaurant=restaurant)
    notification = Notification.objects.create(
        table=table,
        order=order,
        notification_type=Notification.NotificationType.TABLE_ATTENTION,
        message='Table T1 needs your attention.',
        is_read=False
    )
    assert notification.notification_type == Notification.NotificationType.TABLE_ATTENTION


@pytest.mark.django_db
def test_notification_can_be_marked_as_read():
    # verifies is_read can be set to True when a server dismisses the notification
    restaurant = make_restaurant()
    table = make_table(restaurant)
    order = make_order(restaurant=restaurant)
    notification = Notification.objects.create(
        table=table,
        order=order,
        notification_type=Notification.NotificationType.ORDER_READY,
        message='Ready',
        is_read=False
    )
    notification.is_read = True
    notification.save()
    notification.refresh_from_db()
    assert notification.is_read is True


@pytest.mark.django_db
def test_notification_table_fk_is_nullable():
    # verifies notifications can exist without a table FK for delivery order notifications
    order = make_order()
    notification = Notification.objects.create(
        table=None,
        order=order,
        notification_type=Notification.NotificationType.ORDER_READY,
        message='Delivery order assigned',
        is_read=False
    )
    assert notification.table is None


# ====================== PRE-ORDER TESTS ======================

@pytest.mark.django_db
def test_create_preorder():
    # verifies a pre-order can be created linked to a reservation
    restaurant = make_restaurant()
    table = make_table(restaurant)
    customer = make_customer(username='preordercustomer')
    reservation = Reservation.objects.create(
        customer=customer,
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=Decimal('10.00'),
        status=Reservation.Status.CONFIRMED
    )
    preorder = PreOrder.objects.create(
        reservation=reservation,
        customer=customer,
        restaurant=restaurant,
        status=PreOrder.Status.PENDING
    )
    assert preorder.status == PreOrder.Status.PENDING
    assert preorder.reservation == reservation


@pytest.mark.django_db
def test_preorder_defaults_to_pending():
    # verifies a new pre-order always starts with PENDING status
    restaurant = make_restaurant()
    table = make_table(restaurant)
    customer = make_customer(username='preorderdefault')
    reservation = Reservation.objects.create(
        customer=customer,
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=Decimal('10.00')
    )
    preorder = PreOrder.objects.create(
        reservation=reservation,
        customer=customer,
        restaurant=restaurant
    )
    assert preorder.status == PreOrder.Status.PENDING


@pytest.mark.django_db
def test_preorder_item_links_to_preorder():
    # verifies PreOrderItem can be created and linked to a PreOrder correctly
    restaurant = make_restaurant()
    table = make_table(restaurant)
    customer = make_customer(username='preorderitem')
    reservation = Reservation.objects.create(
        customer=customer,
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=Decimal('10.00')
    )
    preorder = PreOrder.objects.create(
        reservation=reservation, customer=customer, restaurant=restaurant
    )
    item = make_menu_item()
    preorder_item = PreOrderItem.objects.create(
        preorder=preorder,
        menu_item=item,
        quantity=2,
        unit_price=Decimal('12.99')
    )
    assert preorder_item.preorder == preorder
    assert preorder_item.quantity == 2


@pytest.mark.django_db
def test_preorder_can_be_activated():
    # verifies a pre-order status can be changed to ACTIVATED after server activates it
    restaurant = make_restaurant()
    table = make_table(restaurant)
    customer = make_customer(username='preorderactivate')
    reservation = Reservation.objects.create(
        customer=customer,
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=Decimal('10.00')
    )
    preorder = PreOrder.objects.create(
        reservation=reservation, customer=customer, restaurant=restaurant,
        status=PreOrder.Status.PENDING
    )
    preorder.status = PreOrder.Status.ACTIVATED
    preorder.save()
    preorder.refresh_from_db()
    assert preorder.status == PreOrder.Status.ACTIVATED


# ====================== TABLE TRANSFER REQUEST TESTS ======================

@pytest.mark.django_db
def test_create_table_transfer_request():
    # verifies a table transfer request can be created between two servers
    restaurant = make_restaurant()
    table = make_table(restaurant)
    server1 = make_user(username='reqserver1', role=User.Role.SERVER_HOST)
    server2 = make_user(username='reqserver2', role=User.Role.SERVER_HOST)
    transfer = TableTransferRequest.objects.create(
        table=table,
        requesting_server=server1,
        receiving_server=server2,
        status=TableTransferRequest.Status.PENDING
    )
    assert transfer.status == TableTransferRequest.Status.PENDING
    assert transfer.requesting_server == server1
    assert transfer.receiving_server == server2


@pytest.mark.django_db
def test_table_transfer_defaults_to_pending():
    # verifies a new transfer request always starts with PENDING status
    restaurant = make_restaurant()
    table = make_table(restaurant)
    server1 = make_user(username='pendserver1', role=User.Role.SERVER_HOST)
    server2 = make_user(username='pendserver2', role=User.Role.SERVER_HOST)
    transfer = TableTransferRequest.objects.create(
        table=table,
        requesting_server=server1,
        receiving_server=server2
    )
    assert transfer.status == TableTransferRequest.Status.PENDING


@pytest.mark.django_db
def test_table_transfer_can_be_accepted():
    # verifies a transfer request status can be set to ACCEPTED
    restaurant = make_restaurant()
    table = make_table(restaurant)
    server1 = make_user(username='accserver1', role=User.Role.SERVER_HOST)
    server2 = make_user(username='accserver2', role=User.Role.SERVER_HOST)
    transfer = TableTransferRequest.objects.create(
        table=table,
        requesting_server=server1,
        receiving_server=server2,
        status=TableTransferRequest.Status.PENDING
    )
    transfer.status = TableTransferRequest.Status.ACCEPTED
    transfer.save()
    transfer.refresh_from_db()
    assert transfer.status == TableTransferRequest.Status.ACCEPTED


@pytest.mark.django_db
def test_table_transfer_can_be_declined():
    # verifies a transfer request status can be set to DECLINED
    restaurant = make_restaurant()
    table = make_table(restaurant)
    server1 = make_user(username='decserver1', role=User.Role.SERVER_HOST)
    server2 = make_user(username='decserver2', role=User.Role.SERVER_HOST)
    transfer = TableTransferRequest.objects.create(
        table=table,
        requesting_server=server1,
        receiving_server=server2,
        status=TableTransferRequest.Status.PENDING
    )
    transfer.status = TableTransferRequest.Status.DECLINED
    transfer.save()
    transfer.refresh_from_db()
    assert transfer.status == TableTransferRequest.Status.DECLINED


# ====================== MANAGER NOTE TESTS ======================

@pytest.mark.django_db
def test_create_manager_note():
    # verifies a manager note can be created with a message and target role
    restaurant = make_restaurant()
    manager = make_user(username='notemgr', role=User.Role.MANAGER)
    note = ManagerNote.objects.create(
        restaurant=restaurant,
        created_by=manager,
        message='Kitchen closes 30 mins early tonight.',
        target_role=0,
        expires_at=timezone.now() + datetime.timedelta(hours=24)
    )
    assert note.message == 'Kitchen closes 30 mins early tonight.'
    assert note.target_role == 0


@pytest.mark.django_db
def test_manager_note_expires_in_future():
    # verifies the expires_at field saves with a future datetime correctly
    restaurant = make_restaurant()
    manager = make_user(username='expiremgr', role=User.Role.MANAGER)
    note = ManagerNote.objects.create(
        restaurant=restaurant,
        created_by=manager,
        message='Test expiry',
        target_role=0,
        expires_at=timezone.now() + datetime.timedelta(hours=24)
    )
    assert note.expires_at > timezone.now()


@pytest.mark.django_db
def test_manager_note_targeted_at_specific_role():
    # verifies notes can be targeted at a specific role such as kitchen staff only
    restaurant = make_restaurant()
    manager = make_user(username='rolemgr', role=User.Role.MANAGER)
    note = ManagerNote.objects.create(
        restaurant=restaurant,
        created_by=manager,
        message='Kitchen only message',
        target_role=User.Role.KITCHEN_STAFF,
        expires_at=timezone.now() + datetime.timedelta(hours=24)
    )
    assert note.target_role == User.Role.KITCHEN_STAFF


@pytest.mark.django_db
def test_manager_note_deleted_when_restaurant_deleted():
    # verifies notes are deleted when their restaurant is deleted (CASCADE)
    restaurant = make_restaurant()
    manager = make_user(username='delmgr', role=User.Role.MANAGER)
    ManagerNote.objects.create(
        restaurant=restaurant,
        created_by=manager,
        message='Will be deleted',
        target_role=0,
        expires_at=timezone.now() + datetime.timedelta(hours=24)
    )
    restaurant.delete()
    assert ManagerNote.objects.filter(message='Will be deleted').count() == 0


# ====================== USER MODEL TESTS ======================

@pytest.mark.django_db
def test_user_role_choices_are_correct():
    # verifies all six expected role values exist on the User model
    roles = [r.value for r in User.Role]
    assert User.Role.MANAGER in roles
    assert User.Role.SERVER_HOST in roles
    assert User.Role.KITCHEN_STAFF in roles
    assert User.Role.DELIVERY_DRIVER in roles
    assert User.Role.CUSTOMER in roles
    assert User.Role.OWNER in roles


@pytest.mark.django_db
def test_user_shift_end_before_start_raises_validation_error():
    # verifies the clean() method on User rejects shift_end before shift_start
    user = User(
        username='badshift',
        role=User.Role.SERVER_HOST,
        shift_start=datetime.time(18, 0),
        shift_end=datetime.time(9, 0)
    )
    with pytest.raises(ValidationError):
        user.clean()


@pytest.mark.django_db
def test_user_str_returns_full_name():
    # verifies the string representation of a user is first name + last name
    user = User.objects.create_user(
        username='fullnameuser', password='TestPass123!', role=User.Role.MANAGER
    )
    user.first_name = 'Bruce'
    user.last_name = 'Wayne'
    user.save()
    assert str(user) == 'Bruce Wayne'


@pytest.mark.django_db
def test_is_active_staff_defaults_to_true():
    # verifies is_active_staff defaults to True for all new staff users
    user = make_user(username='activestafftest', role=User.Role.SERVER_HOST)
    assert user.is_active_staff is True