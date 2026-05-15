import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Python_Project.settings')
django.setup()

from django.utils import timezone # noqa: E402
from restaurant.models import ( # noqa: E402
    User, Customer, Restaurant, Category, Tag,
    MenuItem, RestaurantMenuItem, MenuItemTag,
    Table, StaffInvite, Inventory, Order, Reservation, TableLayout
    )


# ====================== CLEAR EXISTING DATA ======================
# Clears all tables before seeding to prevent duplicate data errors on re-runs
# Preserves superuser accounts (admin panel access) so we don't lock ourselves out

print("Clearing existing data...")

# order matters here — delete children before parents to avoid FK constraint errors
Reservation.objects.all().delete()
Order.objects.all().delete()
Inventory.objects.all().delete()
StaffInvite.objects.all().delete()
Table.objects.all().delete()
MenuItemTag.objects.all().delete()
RestaurantMenuItem.objects.all().delete()
MenuItem.objects.all().delete()
Category.objects.all().delete()
Tag.objects.all().delete()
Restaurant.objects.all().delete()
Customer.objects.all().delete()

# deletes all non-superuser accounts — keeps the Django admin user intact
User.objects.filter(is_superuser=False).delete()

print("Done. Starting seed...")


# ====================== USERS ======================
# Creating one of each role so we can test all dashboards and access controls

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

driver = User.objects.create_user(
    username='driver1',
    password='TestPass123!',
    first_name='Steve',
    last_name='Rogers',
    email='steve@urbanspark.com',
    role=User.Role.DELIVERY_DRIVER
)

# two customer accounts — one with enough points to redeem, one with fewer
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


# ====================== CUSTOMERS ======================
# Customer profiles are separate from User — linked via OneToOneField
# customer1 has 1500 points (enough to redeem either tier)
# customer2 has 500 points (not enough to redeem)

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


# ====================== RESTAURANT ======================
# Single restaurant location for the franchise — linked to manager as the owning user

restaurant = Restaurant.objects.create(
    user=manager,
    name='Urban Spark Downtown',
    address='300 Centre St, Calgary, AB',
    phone_number='403-555-0001',
    opening_time='09:00',
    closing_time='22:00',
    latitude=51.044733,
    longitude=-114.071883,
    is_active=True
)


# ====================== CATEGORIES ======================
# Used to group menu items on the menu page

cat_burgers = Category.objects.create(name='Burgers')
cat_drinks = Category.objects.create(name='Drinks')
cat_sides = Category.objects.create(name='Sides')
cat_desserts = Category.objects.create(name='Desserts')


# ====================== TAGS ======================
# Tags are optional labels on menu items — e.g. dietary info or popularity markers

tag_vegan = Tag.objects.create(name='Vegan')
tag_gluten_free = Tag.objects.create(name='Gluten Free')
tag_spicy = Tag.objects.create(name='Spicy')
tag_popular = Tag.objects.create(name='Popular')


# ====================== MENU ITEMS ======================
# Items are created globally and then linked to a restaurant via RestaurantMenuItem

item1 = MenuItem.objects.create(
    category=cat_burgers,
    name='Classic Smash Burger',
    description='Double smash patty, cheddar, pickles, house sauce',
    price=14.99
)

item2 = MenuItem.objects.create(
    category=cat_burgers,
    name='Spicy Chicken Burger',
    description='Crispy chicken, sriracha mayo, coleslaw',
    price=13.99
)

item3 = MenuItem.objects.create(
    category=cat_burgers,
    name='Vegan Black Bean Burger',
    description='Black bean patty, avocado, tomato, lettuce',
    price=13.49
)

item4 = MenuItem.objects.create(
    category=cat_sides,
    name='Loaded Fries',
    description='Crispy fries with cheese, bacon, and sour cream',
    price=8.99
)

item5 = MenuItem.objects.create(
    category=cat_sides,
    name='Onion Rings',
    description='Beer battered onion rings with dipping sauce',
    price=6.99
)

item6 = MenuItem.objects.create(
    category=cat_drinks,
    name='Sparkling Lemonade',
    description='House-made lemonade with sparkling water',
    price=4.99
)

item7 = MenuItem.objects.create(
    category=cat_drinks,
    name='Craft Root Beer',
    description='Local craft root beer float',
    price=5.99
)

item8 = MenuItem.objects.create(
    category=cat_desserts,
    name='Chocolate Lava Cake',
    description='Warm chocolate cake with vanilla ice cream',
    price=9.99
)


# ====================== RESTAURANT MENU ITEMS ======================
# Junction table linking each MenuItem to the restaurant
# is_available=True means the item is currently on the menu

for item in [item1, item2, item3, item4, item5, item6, item7, item8]:
    RestaurantMenuItem.objects.create(
        restaurant=restaurant,
        menu_item=item,
        is_available=True
    )


# ====================== MENU ITEM TAGS ======================
# Junction table linking MenuItems to Tags — many-to-many relationship

MenuItemTag.objects.create(menu_item=item1, tag=tag_popular)
MenuItemTag.objects.create(menu_item=item2, tag=tag_spicy)
MenuItemTag.objects.create(menu_item=item3, tag=tag_vegan)
MenuItemTag.objects.create(menu_item=item4, tag=tag_popular)
MenuItemTag.objects.create(menu_item=item5, tag=tag_gluten_free)


# ====================== TABLES ======================
# Mix of statuses to test the server/host dashboard display
# T1 and T2 have a server assigned, others do not

table1 = Table.objects.create(
    restaurant=restaurant,
    label='T1',
    seats=4,
    grid_squares={'x': 2, 'y': 2, 'w':1, 'h':1},
    status=Table.Status.AVAILABLE,
    assigned_server=server
)

table2 = Table.objects.create(
    restaurant=restaurant,
    label='T2',
    seats=4,
    grid_squares={'x': 4, 'y': 2, 'w':1, 'h':1},
    status=Table.Status.OCCUPIED,
    assigned_server=server
)

table3 = Table.objects.create(
    restaurant=restaurant,
    label='T3',
    seats=4,
    grid_squares={'x': 6, 'y': 2, 'w':1, 'h':1},
    status=Table.Status.AVAILABLE
)

table4 = Table.objects.create(
    restaurant=restaurant,
    label='T4',
    seats=4,
    grid_squares={'x': 2, 'y': 4, 'w':1, 'h':1},
    status=Table.Status.RESERVED
)

table5 = Table.objects.create(
    restaurant=restaurant,
    label='T5',
    seats=4,
    grid_squares={'x': 6, 'y': 4, 'w':1, 'h':1},
    status=Table.Status.AVAILABLE
)

table6 = Table.objects.create(
    restaurant=restaurant,
    label='T6',
    seats=4,
    grid_squares={'x': 6, 'y': 4, 'w':1, 'h':1},
    status=Table.Status.NEEDS_CLEANING
)

table7 = Table.objects.create(
    restaurant=restaurant,
    label='T7',
    seats=4,
    grid_squares={'x': 2, 'y': 6, 'w':1, 'h':1},
    status=Table.Status.AVAILABLE
)

table8 = Table.objects.create(
    restaurant=restaurant,
    label='T8',
    seats=4,
    grid_squares={'x': 4, 'y': 6, 'w':1, 'h':1},
    status=Table.Status.OCCUPIED
)

table9 = Table.objects.create(
    restaurant=restaurant,
    label='T9',
    seats=4,
    grid_squares={'x': 6, 'y': 6, 'w':1, 'h':1},
    status=Table.Status.AVAILABLE
)

table10 = Table.objects.create(
    restaurant=restaurant,
    label='T10',
    seats=4,
    grid_squares={'x': 2, 'y': 8, 'w':1, 'h':1},
    status=Table.Status.AVAILABLE
)

table11 = Table.objects.create(
    restaurant=restaurant,
    label='T11',
    seats=4,
    grid_squares={'x': 4, 'y': 8, 'w':1, 'h':1},
    status=Table.Status.RESERVED
)

table12 = Table.objects.create(
    restaurant=restaurant,
    label='T12',
    seats=4,
    grid_squares={'x': 6, 'y': 8, 'w':1, 'h':1},
    status=Table.Status.AVAILABLE
)

table13 = Table.objects.create(
    restaurant=restaurant,
    label='T13',
    seats=8,
    grid_squares={'x': 8, 'y': 8, 'w':2, 'h':2},
    status=Table.Status.OCCUPIED
)

table14 = Table.objects.create(
    restaurant=restaurant,
    label='T14',
    seats=4,
    grid_squares={'x': 11, 'y': 8, 'w':1, 'h':1},
    status=Table.Status.AVAILABLE
)

table15 = Table.objects.create(
    restaurant=restaurant,
    label='T15',
    seats=4,
    grid_squares={'x': 13, 'y': 8, 'w':1, 'h':1},
    status=Table.Status.AVAILABLE
)

table16 = Table.objects.create(
    restaurant=restaurant,
    label='T16',
    seats=6,
    grid_squares={'x': 12, 'y': 4, 'w':2, 'h':1},
    status=Table.Status.AVAILABLE
)

# ====================== TABLE LAYOUT ======================

TableLayout.objects.create(
    restaurant=restaurant,
    uploaded_by=manager,
    grid_data=[
        {'table_id': table1.id, 'label': 'T1', 'seats': 4, 'status': 1, 'x': 2, 'y': 2, 'w': 1, 'h': 1},
        {'table_id': table2.id, 'label': 'T2', 'seats': 4, 'status': 2, 'x': 4, 'y': 2, 'w': 1, 'h': 1},
        {'table_id': table3.id, 'label': 'T3', 'seats': 4, 'status': 1, 'x': 6, 'y': 2, 'w': 1, 'h': 1},
        {'table_id': table4.id, 'label': 'T4', 'seats': 4, 'status': 3, 'x': 2, 'y': 4, 'w': 1, 'h': 1},
        {'table_id': table5.id, 'label': 'T5', 'seats': 4, 'status': 1, 'x': 4, 'y': 4, 'w': 1, 'h': 1},
        {'table_id': table6.id, 'label': 'T6', 'seats': 4, 'status': 4, 'x': 6, 'y': 4, 'w': 1, 'h': 1},
        {'table_id': table7.id, 'label': 'T7', 'seats': 4, 'status': 1, 'x': 2, 'y': 6, 'w': 1, 'h': 1},
        {'table_id': table8.id, 'label': 'T8', 'seats': 4, 'status': 2, 'x': 4, 'y': 6, 'w': 1, 'h': 1},
        {'table_id': table9.id, 'label': 'T9', 'seats': 4, 'status': 1, 'x': 6, 'y': 6, 'w': 1, 'h': 1},
        {'table_id': table10.id, 'label': 'T10', 'seats': 4, 'status': 1, 'x': 2, 'y': 8, 'w': 1, 'h': 1},
        {'table_id': table11.id, 'label': 'T11', 'seats': 4, 'status': 3, 'x': 4, 'y': 8, 'w': 1, 'h': 1},
        {'table_id': table12.id, 'label': 'T12', 'seats': 4, 'status': 1, 'x': 6, 'y': 8, 'w': 1, 'h': 1},
        {'table_id': table13.id, 'label': 'T13', 'seats': 8, 'status': 2, 'x': 8, 'y': 8, 'w': 2, 'h': 2},
        {'table_id': table14.id, 'label': 'T14', 'seats': 4, 'status': 1, 'x': 11, 'y': 8, 'w': 1, 'h': 1},
        {'table_id': table15.id, 'label': 'T15', 'seats': 4, 'status': 1, 'x': 13, 'y': 8, 'w': 1, 'h': 1},
        {'table_id': table16.id, 'label': 'T16', 'seats': 6, 'status': 1, 'x': 12, 'y': 4, 'w': 2, 'h': 1},
    ]
)

# ====================== INVENTORY ======================
# Two items are intentionally seeded below their reorder level
# to test the low stock flag in the inventory list view

Inventory.objects.create(
    restaurant=restaurant,
    ingredient_name='Beef Patties',
    current_level=50,
    unit='kg',
    reorder_level=10  # healthy stock
)

Inventory.objects.create(
    restaurant=restaurant,
    ingredient_name='Burger Buns',
    current_level=8,
    unit='units',
    reorder_level=20  # LOW STOCK — current below reorder level
)

Inventory.objects.create(
    restaurant=restaurant,
    ingredient_name='Cheddar Cheese',
    current_level=15,
    unit='kg',
    reorder_level=5  # healthy stock
)

Inventory.objects.create(
    restaurant=restaurant,
    ingredient_name='Sriracha Sauce',
    current_level=3,
    unit='litres',
    reorder_level=4  # LOW STOCK — current below reorder level
)

Inventory.objects.create(
    restaurant=restaurant,
    ingredient_name='Potatoes',
    current_level=80,
    unit='kg',
    reorder_level=15  # healthy stock
)


# ====================== STAFF INVITES ======================
# Pre-approved emails that can register as staff via the staff signup page

StaffInvite.objects.create(
    email='newserver@urbanspark.com',
    role=User.Role.SERVER_HOST
)

StaffInvite.objects.create(
    email='newkitchen@urbanspark.com',
    role=User.Role.KITCHEN_STAFF
)


# ====================== ORDERS ======================
# Three orders covering all three order types
# order1 — dine in, currently being prepared by kitchen
# order2 — delivery, ready and assigned to a driver
# order3 — take out, guest order (no customer linked)

order1 = Order.objects.create(
    customer=customer1,
    restaurant=restaurant,
    order_type=Order.OrderType.DINE_IN,
    sub_total=28.98,
    total_price=28.98,
    order_status=Order.OrderStatus.PREPARING,
    payment_status=Order.PaymentStatus.UNPAID,
    assigned_server=server
)

order2 = Order.objects.create(
    customer=customer2,
    restaurant=restaurant,
    order_type=Order.OrderType.DELIVERY,
    delivery_address='200 Elm Ave, Calgary, AB',
    delivery_fee=10.00,
    sub_total=19.98,
    total_price=29.98,
    order_status=Order.OrderStatus.READY,
    payment_status=Order.PaymentStatus.UNPAID,
    assigned_driver=driver
)

order3 = Order.objects.create(
    customer=None,  # guest order — no customer linked
    restaurant=restaurant,
    order_type=Order.OrderType.TAKE_OUT,
    sub_total=13.99,
    total_price=13.99,
    order_status=Order.OrderStatus.PENDING,
    payment_status=Order.PaymentStatus.UNPAID
)


# ====================== RESERVATIONS ======================
# Three reservations — confirmed customer, pending customer, and a guest walk-in
# Spread across different future times to avoid conflict detection triggering

Reservation.objects.create(
    customer=customer1,
    table=table3,
    restaurant=restaurant,
    reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
    party_size=4,
    deposit_amount=10,
    status=Reservation.Status.CONFIRMED
)

Reservation.objects.create(
    customer=customer2,
    table=table4,
    restaurant=restaurant,
    reservation_datetime=timezone.now() + timezone.timedelta(days=1),
    party_size=2,
    deposit_amount=10,
    status=Reservation.Status.PENDING
)

Reservation.objects.create(
    guest_name='Barry Allen',
    guest_email='barry@email.com',
    guest_phone_number='4037778888',
    table=table13,
    restaurant=restaurant,
    reservation_datetime=timezone.now() + timezone.timedelta(days=2),
    party_size=8,
    deposit_amount=10,
    status=Reservation.Status.PENDING
)


# ====================== SUMMARY ======================

print("Seed complete!")
print(f"  Users created:        {User.objects.filter(is_superuser=False).count()}")
print(f"  Restaurants:          {Restaurant.objects.count()}")
print(f"  Menu Items:           {MenuItem.objects.count()}")
print(f"  Tables:               {Table.objects.count()}")
print(f"  Inventory items:      {Inventory.objects.count()}")
print(f"  Orders:               {Order.objects.count()}")
print(f"  Reservations:         {Reservation.objects.count()}")
print(f"  Staff Invites:        {StaffInvite.objects.count()}")