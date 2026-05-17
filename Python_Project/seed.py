import os
import django
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Python_Project.settings')
django.setup()

from django.utils import timezone  # noqa: E402
from decimal import Decimal  # noqa: E402
from restaurant.models import (  # noqa: E402
    User, Customer, Restaurant, Category, Tag,
    MenuItem, RestaurantMenuItem, MenuItemTag,
    Table, TableLayout, StaffInvite, Inventory,
    Order, OrderItem, Payment, Reservation,
    Notification, PreOrder, PreOrderItem,
    TableTransferRequest, ManagerNote
)


# ====================== CLEAR EXISTING DATA ======================
# Clears all tables before seeding to prevent duplicate data errors on re-runs
# Preserves superuser accounts (admin panel access) so we do not lock ourselves out
# Order matters: delete children before parents to avoid FK constraint errors

print("Clearing existing data...")

ManagerNote.objects.all().delete()
TableTransferRequest.objects.all().delete()
Notification.objects.all().delete()
PreOrderItem.objects.all().delete()
PreOrder.objects.all().delete()
Payment.objects.all().delete()
OrderItem.objects.all().delete()
Order.objects.all().delete()
Reservation.objects.all().delete()
TableLayout.objects.all().delete()
Table.objects.all().delete()
Inventory.objects.all().delete()
StaffInvite.objects.all().delete()
MenuItemTag.objects.all().delete()
RestaurantMenuItem.objects.all().delete()
MenuItem.objects.all().delete()
Category.objects.all().delete()
Tag.objects.all().delete()
Restaurant.objects.all().delete()
Customer.objects.all().delete()

# deletes all non-superuser accounts, keeps the Django admin user intact
User.objects.filter(is_superuser=False).delete()

print("Done. Starting seed...")


# ====================== USERS ======================
# Creating one of each role so we can test all dashboards and access controls
# Passwords are all TestPass123! for easy testing

owner = User.objects.create_user(
    username='owner1',
    password='TestPass123!',
    first_name='Diana',
    last_name='Prince',
    email='diana@urbanspark.com',
    role=User.Role.OWNER
)

manager = User.objects.create_user(
    username='manager1',
    password='TestPass123!',
    first_name='Bruce',
    last_name='Wayne',
    email='bruce@urbanspark.com',
    role=User.Role.MANAGER
)

# server1 is assigned to T1 and T2 to test the server host dashboard
server = User.objects.create_user(
    username='server1',
    password='TestPass123!',
    first_name='Peter',
    last_name='Parker',
    email='peter@urbanspark.com',
    role=User.Role.SERVER_HOST,
    shift_start='09:00',
    shift_end='17:00'
)

# server2 is used to test table transfer requests between servers
server2 = User.objects.create_user(
    username='server2',
    password='TestPass123!',
    first_name='Natasha',
    last_name='Romanoff',
    email='natasha@urbanspark.com',
    role=User.Role.SERVER_HOST,
    shift_start='12:00',
    shift_end='20:00'
)

kitchen = User.objects.create_user(
    username='kitchen1',
    password='TestPass123!',
    first_name='Tony',
    last_name='Stark',
    email='tony@urbanspark.com',
    role=User.Role.KITCHEN_STAFF,
    shift_start='10:00',
    shift_end='18:00'
)

# driver1 and driver2 are used to test round-robin auto-assignment on delivery orders
driver = User.objects.create_user(
    username='driver1',
    password='TestPass123!',
    first_name='Steve',
    last_name='Rogers',
    email='steve@urbanspark.com',
    role=User.Role.DELIVERY_DRIVER
)

driver2 = User.objects.create_user(
    username='driver2',
    password='TestPass123!',
    first_name='Sam',
    last_name='Wilson',
    email='sam@urbanspark.com',
    role=User.Role.DELIVERY_DRIVER
)

# customer1 has 1500 points (enough to redeem $10 off but not $25 off)
# customer2 has 500 points (not enough to redeem anything)
# customer3 has 2500 points (enough to redeem $25 off)
customer_user1 = User.objects.create_user(
    username='customer1',
    password='TestPass123!',
    first_name='Clark',
    last_name='Kent',
    email='clark@email.com',
    role=User.Role.CUSTOMER
)

customer_user2 = User.objects.create_user(
    username='customer2',
    password='TestPass123!',
    first_name='Lois',
    last_name='Lane',
    email='lois@email.com',
    role=User.Role.CUSTOMER
)

customer_user3 = User.objects.create_user(
    username='customer3',
    password='TestPass123!',
    first_name='Barry',
    last_name='Allen',
    email='barry@email.com',
    role=User.Role.CUSTOMER
)


# ====================== CUSTOMERS ======================
# Customer profiles are separate from User, linked via OneToOneField
# Points are set to test all three redemption tiers in order_create

customer1 = Customer.objects.create(
    user=customer_user1,
    phone_number='4031112222',
    address='100 Main St, Calgary, AB',
    loyalty_points=1500
)

customer2 = Customer.objects.create(
    user=customer_user2,
    phone_number='4033334444',
    address='200 Elm Ave, Calgary, AB',
    loyalty_points=500
)

customer3 = Customer.objects.create(
    user=customer_user3,
    phone_number='4035556666',
    address='300 River Rd, Calgary, AB',
    loyalty_points=2500
)


# ====================== RESTAURANT ======================
# Single restaurant location for the franchise
# Linked to manager as the owning user so manager_view scopes correctly
# Coordinates are real Calgary downtown coordinates for delivery distance validation

restaurant = Restaurant.objects.create(
    user=manager,
    name='Urban Spark Downtown',
    address='300 Centre St, Calgary, AB',
    phone_number='403-555-0001',
    opening_time='09:00',
    closing_time='22:00',
    latitude=Decimal('51.044733'),
    longitude=Decimal('-114.071883'),
    is_active=True
)


# ====================== CATEGORIES ======================
# Used to group menu items on the menu page and in reporting

cat_burgers = Category.objects.create(name='Burgers')
cat_drinks = Category.objects.create(name='Drinks')
cat_sides = Category.objects.create(name='Sides')
cat_desserts = Category.objects.create(name='Desserts')
cat_appetizers = Category.objects.create(name='Appetizers')


# ====================== TAGS ======================
# Optional labels on menu items for dietary info and popularity markers
# Tag CSS classes in style.css use slugified versions of these names

tag_vegan = Tag.objects.create(name='Vegan')
tag_gluten_free = Tag.objects.create(name='Gluten Free')
tag_spicy = Tag.objects.create(name='Spicy')
tag_popular = Tag.objects.create(name='Popular')
tag_nuts = Tag.objects.create(name='Contains Nuts')


# ====================== MENU ITEMS ======================
# Items are created globally and then linked to a restaurant via RestaurantMenuItem
# item1 is seeded as unavailable to test the greyed out menu item feature

item1 = MenuItem.objects.create(
    category=cat_burgers,
    name='Classic Smash Burger',
    description='Double smash patty, cheddar, pickles, house sauce',
    price=Decimal('14.99')
)

item2 = MenuItem.objects.create(
    category=cat_burgers,
    name='Spicy Chicken Burger',
    description='Crispy chicken, sriracha mayo, coleslaw',
    price=Decimal('13.99')
)

item3 = MenuItem.objects.create(
    category=cat_burgers,
    name='Vegan Black Bean Burger',
    description='Black bean patty, avocado, tomato, lettuce',
    price=Decimal('13.49')
)

item4 = MenuItem.objects.create(
    category=cat_sides,
    name='Loaded Fries',
    description='Crispy fries with cheese, bacon, and sour cream',
    price=Decimal('8.99')
)

item5 = MenuItem.objects.create(
    category=cat_sides,
    name='Onion Rings',
    description='Beer battered onion rings with dipping sauce',
    price=Decimal('6.99')
)

item6 = MenuItem.objects.create(
    category=cat_drinks,
    name='Sparkling Lemonade',
    description='House-made lemonade with sparkling water',
    price=Decimal('4.99')
)

item7 = MenuItem.objects.create(
    category=cat_drinks,
    name='Craft Root Beer',
    description='Local craft root beer float',
    price=Decimal('5.99')
)

item8 = MenuItem.objects.create(
    category=cat_desserts,
    name='Chocolate Lava Cake',
    description='Warm chocolate cake with vanilla ice cream',
    price=Decimal('9.99')
)

item9 = MenuItem.objects.create(
    category=cat_appetizers,
    name='Garlic Bread',
    description='Toasted sourdough with roasted garlic butter and herbs',
    price=Decimal('6.49')
)

item10 = MenuItem.objects.create(
    category=cat_appetizers,
    name='Calamari',
    description='Lightly breaded calamari rings with marinara sauce',
    price=Decimal('11.99')
)

item11 = MenuItem.objects.create(
    category=cat_burgers,
    name='Signature Steak Burger',
    description='6oz ribeye patty, aged cheddar, caramelized onions, truffle aioli',
    price=Decimal('18.99')
)


# ====================== RESTAURANT MENU ITEMS ======================
# Junction table linking each MenuItem to the restaurant
# item1 is seeded as unavailable to test the greyed out card and Mark Available button

RestaurantMenuItem.objects.create(
    restaurant=restaurant,
    menu_item=item1,
    is_available=False  # intentionally unavailable to test the toggle feature
)

for item in [item2, item3, item4, item5, item6, item7, item8, item9, item10, item11]:
    RestaurantMenuItem.objects.create(
        restaurant=restaurant,
        menu_item=item,
        is_available=True
    )


# ====================== MENU ITEM TAGS ======================
# Junction table linking MenuItems to Tags, many-to-many relationship

MenuItemTag.objects.create(menu_item=item1, tag=tag_popular)
MenuItemTag.objects.create(menu_item=item2, tag=tag_spicy)
MenuItemTag.objects.create(menu_item=item3, tag=tag_vegan)
MenuItemTag.objects.create(menu_item=item3, tag=tag_gluten_free)
MenuItemTag.objects.create(menu_item=item4, tag=tag_popular)
MenuItemTag.objects.create(menu_item=item5, tag=tag_gluten_free)
MenuItemTag.objects.create(menu_item=item9, tag=tag_popular)
MenuItemTag.objects.create(menu_item=item10, tag=tag_nuts)
MenuItemTag.objects.create(menu_item=item11, tag=tag_popular)


# ====================== TABLES ======================
# 16 tables covering all 4 status types to test server host dashboard colour coding
# T1 and T2 are assigned to server1 to test assigned table cards and grid highlighting
# T3 is assigned to server2 to test the transfer request flow
# Grid coordinates are intentional and match the TableLayout seed below

table1 = Table.objects.create(
    restaurant=restaurant,
    label='T1',
    seats=4,
    grid_squares={'x': 2, 'y': 2, 'w': 1, 'h': 1},
    status=Table.Status.OCCUPIED,
    assigned_server=server
)

table2 = Table.objects.create(
    restaurant=restaurant,
    label='T2',
    seats=4,
    grid_squares={'x': 4, 'y': 2, 'w': 1, 'h': 1},
    status=Table.Status.AVAILABLE,
    assigned_server=server
)

table3 = Table.objects.create(
    restaurant=restaurant,
    label='T3',
    seats=4,
    grid_squares={'x': 6, 'y': 2, 'w': 1, 'h': 1},
    status=Table.Status.RESERVED,
    assigned_server=server2
)

table4 = Table.objects.create(
    restaurant=restaurant,
    label='T4',
    seats=4,
    grid_squares={'x': 2, 'y': 4, 'w': 1, 'h': 1},
    status=Table.Status.RESERVED
)

table5 = Table.objects.create(
    restaurant=restaurant,
    label='T5',
    seats=4,
    grid_squares={'x': 4, 'y': 4, 'w': 1, 'h': 1},
    status=Table.Status.AVAILABLE
)

table6 = Table.objects.create(
    restaurant=restaurant,
    label='T6',
    seats=4,
    grid_squares={'x': 6, 'y': 4, 'w': 1, 'h': 1},
    status=Table.Status.NEEDS_CLEANING
)

table7 = Table.objects.create(
    restaurant=restaurant,
    label='T7',
    seats=4,
    grid_squares={'x': 2, 'y': 6, 'w': 1, 'h': 1},
    status=Table.Status.AVAILABLE
)

table8 = Table.objects.create(
    restaurant=restaurant,
    label='T8',
    seats=4,
    grid_squares={'x': 4, 'y': 6, 'w': 1, 'h': 1},
    status=Table.Status.OCCUPIED
)

table9 = Table.objects.create(
    restaurant=restaurant,
    label='T9',
    seats=4,
    grid_squares={'x': 6, 'y': 6, 'w': 1, 'h': 1},
    status=Table.Status.AVAILABLE
)

table10 = Table.objects.create(
    restaurant=restaurant,
    label='T10',
    seats=4,
    grid_squares={'x': 2, 'y': 8, 'w': 1, 'h': 1},
    status=Table.Status.AVAILABLE
)

table11 = Table.objects.create(
    restaurant=restaurant,
    label='T11',
    seats=4,
    grid_squares={'x': 4, 'y': 8, 'w': 1, 'h': 1},
    status=Table.Status.RESERVED
)

table12 = Table.objects.create(
    restaurant=restaurant,
    label='T12',
    seats=4,
    grid_squares={'x': 6, 'y': 8, 'w': 1, 'h': 1},
    status=Table.Status.AVAILABLE
)

table13 = Table.objects.create(
    restaurant=restaurant,
    label='T13',
    seats=8,
    grid_squares={'x': 8, 'y': 8, 'w': 2, 'h': 2},
    status=Table.Status.OCCUPIED
)

table14 = Table.objects.create(
    restaurant=restaurant,
    label='T14',
    seats=4,
    grid_squares={'x': 11, 'y': 8, 'w': 1, 'h': 1},
    status=Table.Status.AVAILABLE
)

table15 = Table.objects.create(
    restaurant=restaurant,
    label='T15',
    seats=4,
    grid_squares={'x': 13, 'y': 8, 'w': 1, 'h': 1},
    status=Table.Status.AVAILABLE
)

table16 = Table.objects.create(
    restaurant=restaurant,
    label='T16',
    seats=6,
    grid_squares={'x': 12, 'y': 4, 'w': 2, 'h': 1},
    status=Table.Status.AVAILABLE
)


# ====================== TABLE LAYOUT ======================
# Saves the floor plan grid snapshot so server host dashboard can render it read-only
# Grid coordinates must match the grid_squares on each table above
# Status values in grid_data reflect the initial seeded status of each table

TableLayout.objects.create(
    restaurant=restaurant,
    uploaded_by=manager,
    grid_data=[
        {'table_id': table1.id,  'label': 'T1',  'seats': 4, 'status': 2, 'x': 2,  'y': 2, 'w': 1, 'h': 1},
        {'table_id': table2.id,  'label': 'T2',  'seats': 4, 'status': 1, 'x': 4,  'y': 2, 'w': 1, 'h': 1},
        {'table_id': table3.id,  'label': 'T3',  'seats': 4, 'status': 3, 'x': 6,  'y': 2, 'w': 1, 'h': 1},
        {'table_id': table4.id,  'label': 'T4',  'seats': 4, 'status': 3, 'x': 2,  'y': 4, 'w': 1, 'h': 1},
        {'table_id': table5.id,  'label': 'T5',  'seats': 4, 'status': 1, 'x': 4,  'y': 4, 'w': 1, 'h': 1},
        {'table_id': table6.id,  'label': 'T6',  'seats': 4, 'status': 4, 'x': 6,  'y': 4, 'w': 1, 'h': 1},
        {'table_id': table7.id,  'label': 'T7',  'seats': 4, 'status': 1, 'x': 2,  'y': 6, 'w': 1, 'h': 1},
        {'table_id': table8.id,  'label': 'T8',  'seats': 4, 'status': 2, 'x': 4,  'y': 6, 'w': 1, 'h': 1},
        {'table_id': table9.id,  'label': 'T9',  'seats': 4, 'status': 1, 'x': 6,  'y': 6, 'w': 1, 'h': 1},
        {'table_id': table10.id, 'label': 'T10', 'seats': 4, 'status': 1, 'x': 2,  'y': 8, 'w': 1, 'h': 1},
        {'table_id': table11.id, 'label': 'T11', 'seats': 4, 'status': 3, 'x': 4,  'y': 8, 'w': 1, 'h': 1},
        {'table_id': table12.id, 'label': 'T12', 'seats': 4, 'status': 1, 'x': 6,  'y': 8, 'w': 1, 'h': 1},
        {'table_id': table13.id, 'label': 'T13', 'seats': 8, 'status': 2, 'x': 8,  'y': 8, 'w': 1, 'h': 1},
        {'table_id': table14.id, 'label': 'T14', 'seats': 4, 'status': 1, 'x': 11, 'y': 8, 'w': 1, 'h': 1},
        {'table_id': table15.id, 'label': 'T15', 'seats': 4, 'status': 1, 'x': 13, 'y': 8, 'w': 1, 'h': 1},
        {'table_id': table16.id, 'label': 'T16', 'seats': 6, 'status': 1, 'x': 11, 'y': 4, 'w': 2, 'h': 1},
    ]
)


# ====================== INVENTORY ======================
# Two items are intentionally below their reorder level to test the low stock alert banner
# Reorder levels are set so the flag fires clearly in the inventory list view

Inventory.objects.create(
    restaurant=restaurant,
    ingredient_name='Beef Patties',
    current_level=Decimal('50.00'),
    unit='kg',
    reorder_level=Decimal('10.00')  # healthy stock
)

Inventory.objects.create(
    restaurant=restaurant,
    ingredient_name='Burger Buns',
    current_level=Decimal('8.00'),
    unit='units',
    reorder_level=Decimal('20.00')  # LOW STOCK, current is below reorder level
)

Inventory.objects.create(
    restaurant=restaurant,
    ingredient_name='Cheddar Cheese',
    current_level=Decimal('15.00'),
    unit='kg',
    reorder_level=Decimal('5.00')  # healthy stock
)

Inventory.objects.create(
    restaurant=restaurant,
    ingredient_name='Sriracha Sauce',
    current_level=Decimal('3.00'),
    unit='litres',
    reorder_level=Decimal('4.00')  # LOW STOCK, current is below reorder level
)

Inventory.objects.create(
    restaurant=restaurant,
    ingredient_name='Potatoes',
    current_level=Decimal('80.00'),
    unit='kg',
    reorder_level=Decimal('15.00')  # healthy stock
)

Inventory.objects.create(
    restaurant=restaurant,
    ingredient_name='Brioche Buns',
    current_level=Decimal('40.00'),
    unit='units',
    reorder_level=Decimal('10.00')  # healthy stock
)


# ====================== STAFF INVITES ======================
# Pre-approved emails that can register as staff via the staff signup page
# Covers all non-customer roles so each signup flow can be tested

StaffInvite.objects.create(
    email='newserver@urbanspark.com',
    role=User.Role.SERVER_HOST
)

StaffInvite.objects.create(
    email='newkitchen@urbanspark.com',
    role=User.Role.KITCHEN_STAFF
)

StaffInvite.objects.create(
    email='newdriver@urbanspark.com',
    role=User.Role.DELIVERY_DRIVER
)

StaffInvite.objects.create(
    email='newmanager@urbanspark.com',
    role=User.Role.MANAGER
)


# ====================== ORDERS ======================
# Five orders covering all order types, payment states, and status transitions
# order1: dine-in, paid, preparing, linked to table1 and server1
# order2: delivery, unpaid, ready, auto-assigned to driver1 to test driver dashboard
# order3: takeout, guest (no customer), pending, unpaid
# order4: dine-in, paid, completed, linked to customer3 to test loyalty history
# order5: delivery, paid, completed, linked to customer2 to test driver history

order1 = Order.objects.create(
    customer=customer1,
    restaurant=restaurant,
    table=table1,
    order_type=Order.OrderType.DINE_IN,
    sub_total=Decimal('28.98'),
    tax_amount=Decimal('1.45'),
    total_price=Decimal('30.43'),
    order_status=Order.OrderStatus.PREPARING,
    payment_status=Order.PaymentStatus.PAID,
    assigned_server=server
)

order2 = Order.objects.create(
    customer=customer2,
    restaurant=restaurant,
    order_type=Order.OrderType.DELIVERY,
    delivery_address='200 Elm Ave, Calgary, AB',
    delivery_fee=Decimal('10.00'),
    sub_total=Decimal('19.98'),
    tax_amount=Decimal('1.50'),
    total_price=Decimal('31.48'),
    order_status=Order.OrderStatus.READY,
    payment_status=Order.PaymentStatus.PAID,
    assigned_driver=driver
)

order3 = Order.objects.create(
    customer=None,  # guest order, no customer linked
    restaurant=restaurant,
    order_type=Order.OrderType.TAKE_OUT,
    sub_total=Decimal('13.99'),
    tax_amount=Decimal('0.70'),
    total_price=Decimal('14.69'),
    order_status=Order.OrderStatus.PENDING,
    payment_status=Order.PaymentStatus.UNPAID,
    special_instruction='Guest: John Doe | Phone: 4031234567'
)

order4 = Order.objects.create(
    customer=customer3,
    restaurant=restaurant,
    table=table8,
    order_type=Order.OrderType.DINE_IN,
    sub_total=Decimal('43.97'),
    tax_amount=Decimal('2.20'),
    total_price=Decimal('46.17'),
    order_status=Order.OrderStatus.COMPLETED,
    payment_status=Order.PaymentStatus.PAID,
    assigned_server=server2,
    points_earned=430,
    points_redeemed=0
)

order5 = Order.objects.create(
    customer=customer2,
    restaurant=restaurant,
    order_type=Order.OrderType.DELIVERY,
    delivery_address='200 Elm Ave, Calgary, AB',
    delivery_fee=Decimal('5.00'),
    sub_total=Decimal('14.99'),
    tax_amount=Decimal('1.00'),
    total_price=Decimal('20.99'),
    order_status=Order.OrderStatus.COMPLETED,
    payment_status=Order.PaymentStatus.PAID,
    assigned_driver=driver,
    points_earned=140
)


# ====================== ORDER ITEMS ======================
# Line items for each order above
# These mirror real menu choices to make the kitchen and server views look realistic

# order1: dine-in for customer1 at T1
OrderItem.objects.create(order=order1, menu_item=item1, quantity=1, unit_price=Decimal('14.99'))
OrderItem.objects.create(order=order1, menu_item=item4, quantity=1, unit_price=Decimal('8.99'))
OrderItem.objects.create(order=order1, menu_item=item6, quantity=1, unit_price=Decimal('4.99'))

# order2: delivery for customer2
OrderItem.objects.create(order=order2, menu_item=item2, quantity=1, unit_price=Decimal('13.99'))
OrderItem.objects.create(order=order2, menu_item=item5, quantity=1, unit_price=Decimal('6.99'))

# order3: guest takeout
OrderItem.objects.create(order=order3, menu_item=item3, quantity=1, unit_price=Decimal('13.99'))

# order4: completed dine-in for customer3 at T8
OrderItem.objects.create(order=order4, menu_item=item11, quantity=1, unit_price=Decimal('18.99'))
OrderItem.objects.create(order=order4, menu_item=item9,  quantity=2, unit_price=Decimal('6.49'))
OrderItem.objects.create(order=order4, menu_item=item8,  quantity=1, unit_price=Decimal('9.99'))

# order5: completed delivery for customer2
OrderItem.objects.create(order=order5, menu_item=item1, quantity=1, unit_price=Decimal('14.99'))


# ====================== PAYMENTS ======================
# Payment records for all paid orders
# Transaction IDs use a fake prefix so they are clearly test data

Payment.objects.create(
    order=order1,
    method=Payment.PaymentMethod.CREDIT_CARD,
    amount=Decimal('30.43'),
    transaction_id='pi_test_order1_clark_dinein',
    status='succeeded'
)

Payment.objects.create(
    order=order2,
    method=Payment.PaymentMethod.CREDIT_CARD,
    amount=Decimal('31.48'),
    transaction_id='pi_test_order2_lois_delivery',
    status='succeeded'
)

Payment.objects.create(
    order=order4,
    method=Payment.PaymentMethod.CREDIT_CARD,
    amount=Decimal('46.17'),
    transaction_id='pi_test_order4_barry_dinein',
    status='succeeded'
)

Payment.objects.create(
    order=order5,
    method=Payment.PaymentMethod.CREDIT_CARD,
    amount=Decimal('20.99'),
    transaction_id='pi_test_order5_lois_delivery',
    status='succeeded'
)


# ====================== RESERVATIONS ======================
# Five reservations covering all status types and both customer and guest bookings
# reservation1: confirmed, linked to customer1 at T3, 3hrs from now
# reservation2: pending, linked to customer2 at T4, tomorrow
# reservation3: pending guest, linked to T13, 2 days out
# reservation4: pending, linked to customer3 at T11, has a pre-order attached (seeded below)
# reservation5: cancelled with fee applied to test cancellation display

reservation1 = Reservation.objects.create(
    customer=customer1,
    table=table3,
    restaurant=restaurant,
    reservation_datetime=timezone.make_aware(datetime.datetime(2026, 5, 22, 18, 0)),
    party_size=4,
    deposit_amount=Decimal('10.00'),
    status=Reservation.Status.CONFIRMED
)

reservation2 = Reservation.objects.create(
    customer=customer2,
    table=table4,
    restaurant=restaurant,
    reservation_datetime=timezone.now() + datetime.timedelta(days=1),
    party_size=2,
    deposit_amount=Decimal('10.00'),
    status=Reservation.Status.PENDING
)

reservation3 = Reservation.objects.create(
    guest_name='Wade Wilson',
    guest_email='wade@email.com',
    guest_phone_number='4037778888',
    table=table13,
    restaurant=restaurant,
    reservation_datetime=timezone.now() + datetime.timedelta(days=2),
    party_size=8,
    deposit_amount=Decimal('10.00'),
    status=Reservation.Status.PENDING
)

# reservation4 has a pre-order so we can test server_table_detail activate pre-order
reservation4 = Reservation.objects.create(
    customer=customer3,
    table=table11,
    restaurant=restaurant,
    reservation_datetime=timezone.now() + datetime.timedelta(hours=6),
    party_size=3,
    deposit_amount=Decimal('10.00'),
    status=Reservation.Status.CONFIRMED
)

# reservation5 is cancelled with a fee applied to test the cancellation_fee_applied flag
reservation5 = Reservation.objects.create(
    customer=customer1,
    table=table7,
    restaurant=restaurant,
    reservation_datetime=timezone.now() - datetime.timedelta(hours=1),
    party_size=2,
    deposit_amount=Decimal('10.00'),
    status=Reservation.Status.CANCELLED,
    cancellation_fee_applied=True
)


# ====================== PRE-ORDER ======================
# A pending pre-order linked to reservation4 so server_table_detail shows the activate button
# Special instruction includes an allergy note to test the red highlight in the template

preorder = PreOrder.objects.create(
    reservation=reservation4,
    customer=customer3,
    restaurant=restaurant,
    special_instruction='Allergy: Nuts. Please ensure no cross-contamination.',
    status=PreOrder.Status.PENDING
)

PreOrderItem.objects.create(
    preorder=preorder,
    menu_item=item11,
    quantity=1,
    unit_price=Decimal('18.99')
)

PreOrderItem.objects.create(
    preorder=preorder,
    menu_item=item9,
    quantity=2,
    unit_price=Decimal('6.49')
)


# ====================== NOTIFICATIONS ======================
# Seed one ORDER_READY notification on table1 to test the server dashboard notification bar
# Seed one TABLE_ATTENTION notification on table2 to test the host mode attention request
# Seed one driver assignment notification for order2 to test the driver dashboard

Notification.objects.create(
    table=table1,
    order=order1,
    notification_type=Notification.NotificationType.ORDER_READY,
    message=f'Order #{order1.id} at Table T1 is ready!',
    is_read=False
)

Notification.objects.create(
    table=table2,
    order=order1,
    notification_type=Notification.NotificationType.TABLE_ATTENTION,
    message='Table T2 needs your attention. Requested by host Peter Parker.',
    is_read=False
)

Notification.objects.create(
    table=None,
    order=order2,
    notification_type=Notification.NotificationType.ORDER_READY,
    message=f'Delivery order #{order2.id} has been assigned to you. Please pick up from the kitchen.',
    is_read=False
)


# ====================== TABLE TRANSFER REQUEST ======================
# A pending transfer request from server1 to server2 for table1
# Tests the incoming transfer notification on server2s dashboard

TableTransferRequest.objects.create(
    table=table1,
    requesting_server=server,
    receiving_server=server2,
    status=TableTransferRequest.Status.PENDING
)


# ====================== MANAGER NOTE ======================
# One active note targeting all staff and one targeting kitchen only
# expires_at is set to 24 hours from now so both notes are visible immediately

ManagerNote.objects.create(
    restaurant=restaurant,
    created_by=manager,
    message='Kitchen closing 30 minutes early tonight. Last orders by 9:30 PM.',
    target_role=0,  # 0 means all staff
    expires_at=timezone.now() + datetime.timedelta(hours=24)
)

ManagerNote.objects.create(
    restaurant=restaurant,
    created_by=manager,
    message='New ticket printer installed at station 2. Use station 2 for all dine-in orders today.',
    target_role=User.Role.KITCHEN_STAFF,
    expires_at=timezone.now() + datetime.timedelta(hours=24)
)


# ====================== SUMMARY ======================

print("Seed complete!")
print(f"  Users created:           {User.objects.filter(is_superuser=False).count()}")
print(f"  Customers:               {Customer.objects.count()}")
print(f"  Restaurants:             {Restaurant.objects.count()}")
print(f"  Categories:              {Category.objects.count()}")
print(f"  Tags:                    {Tag.objects.count()}")
print(f"  Menu Items:              {MenuItem.objects.count()}")
print(f"  Tables:                  {Table.objects.count()}")
print(f"  Inventory Items:         {Inventory.objects.count()}")
print(f"  Orders:                  {Order.objects.count()}")
print(f"  Order Items:             {OrderItem.objects.count()}")
print(f"  Payments:                {Payment.objects.count()}")
print(f"  Reservations:            {Reservation.objects.count()}")
print(f"  Pre-Orders:              {PreOrder.objects.count()}")
print(f"  Notifications:           {Notification.objects.count()}")
print(f"  Transfer Requests:       {TableTransferRequest.objects.count()}")
print(f"  Manager Notes:           {ManagerNote.objects.count()}")
print(f"  Staff Invites:           {StaffInvite.objects.count()}")
print()
print("Test logins:")
print("  owner1 / TestPass123!    Owner (Diana Prince)")
print("  manager1 / TestPass123!  Manager (Bruce Wayne)")
print("  server1 / TestPass123!   Server (Peter Parker) assigned T1 and T2")
print("  server2 / TestPass123!   Server (Natasha Romanoff) assigned T3")
print("  kitchen1 / TestPass123!  Kitchen Staff (Tony Stark)")
print("  driver1 / TestPass123!   Driver (Steve Rogers) has active delivery")
print("  driver2 / TestPass123!   Driver (Sam Wilson) no active deliveries")
print("  customer1 / TestPass123! Customer (Clark Kent) 1500 pts")
print("  customer2 / TestPass123! Customer (Lois Lane) 500 pts")
print("  customer3 / TestPass123! Customer (Barry Allen) 2500 pts")