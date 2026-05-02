from django.db import models
from django.contrib.auth.models import AbstractUser
from decimal import Decimal


class User(AbstractUser):
    class Role (models.IntegerChoices):
            MANAGER = 1
            SERVER_HOST = 2
            KITCHEN_STAFF = 3
            DELIVERY_DRIVER = 4
            CUSTOMER = 5

    email = models.EmailField() # field type contains email validation
    role = models.IntegerField(choices=Role.choices) # uses chocies defined in subclass Role
    created_at = models.DateTimeField(auto_now_add=True)


class Category(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class Tag(models.Model):
    name = models.CharField(max_length=100)


class Restaurant(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True) # allows a MANAGER user to be delieted without deleting a restaurant
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    latitude = models.DecimalField(max_digits=8, decimal_places=6)
    longitude = models.DecimalField(max_digits=8, decimal_places=6)
    is_active = models.BooleanField(default=True) # Restaurant defaults to active as soon as it's created


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # FK exists in OneToOneField here, allows one User to have exactly one Customer record
    phone_number = models.CharField(max_length=50)
    address = models.CharField(max_length=255)


class Inventory(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE) # if restaurant is deleted, inventory is deleted with it
    ingredient_name = models.CharField(max_length=100)
    current_level = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    last_updated = models.DateTimeField(auto_now=True) # allows filed to save upon update


class Table(models.Model):
    class Status (models.IntegerChoices):
        AVAILABLE = 1
        OCCUPIED = 2
        RESERVED = 3

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE) # if restaurant is deleted so are its tables
    label = models.CharField(max_length=20)
    seats = models.IntegerField()
    grid_squares = models.JSONField()
    status = models.IntegerField(choices=Status.choices, default=Status.AVAILABLE) # as soon as a new table is created, it's made AVAILABLE.  Uses subclass Status as choices


class TableLayout(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE) # if restaurant is deleted so is its table layout
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    grid_data = models.JSONField()
    uploaded_at = models.DateTimeField(auto_now_add=True)


class MenuItem(models.Model):
    restaurants = models.ManyToManyField(Restaurant, related_name='menu_items') 
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True) # if category is deleted, menuItem is just marked as NULL for this field
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='menu_images/', null=True, blank=True)


class MenuItemTag(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


class Reservation(models.Model):
    class Status (models.IntegerChoices):
        PENDING = 1
        CONFIRMED = 2
        COMPLETED = 3
        CANCELLED = 4

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=255, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)
    guest_phone_number = models.CharField(max_length=100, null=True, blank=True)
    reservation_datetime = models.DateTimeField()
    party_size = models.IntegerField()
    status = models.IntegerField(choices=Status.choices, default=Status.PENDING)
    deposit_amount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10')) # Decimal('10') used instead of 0 to satisfy DecimalField type requirements
    cancellation_fee_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Order(models.Model):
    class OrderType (models.IntegerChoices):
        DINE_IN = 1
        TAKE_OUT = 2
        DELIVERY = 3

    class PaymentStatus (models.IntegerChoices):
        UNPAID = 1
        PAID = 2
        REFUNDED = 3

    class OrderStatus (models.IntegerChoices):
        PENDING = 1
        PREPARING = 2
        READY = 3
        COMPLETED = 4
        CANCELLED = 5

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True) # Customer being Null allows a guest to order
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True) # if a restaurant is deleted, its order history is not
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True)
    assigned_server = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='served_orders')
    assigned_driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='delivered_orders')
    order_type = models.IntegerField(choices=OrderType.choices) 
    delivery_address = models.CharField(max_length=255, null=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    loyalty_discount = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0')) # Decimal('0') used instead of 0 to satisfy DecimalField type requirements
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    special_instruction = models.TextField(null=True, blank=True)
    payment_status = models.IntegerField(choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    order_status = models.IntegerField(choices=OrderStatus.choices, default=OrderStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)


class Payment(models.Model):
    class PaymentMethod (models.IntegerChoices):
        CREDIT_CARD = 1
        MOBILE_WALLET = 2

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    method = models.IntegerField(choices=PaymentMethod.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=50, unique=True)
    processed_at = models.DateTimeField(auto_now_add=True)


class PointsLog(models.Model):
    class TransactionType (models.IntegerChoices):
        EARNED = 1
        REDEEMED = 2

    transaction_type = models.IntegerField(choices=TransactionType.choices)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    points_earned = models.IntegerField(default=0)
    points_redeemed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
