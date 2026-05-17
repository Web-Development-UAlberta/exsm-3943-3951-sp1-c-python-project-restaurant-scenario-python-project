from django.db import models
from django.contrib.auth.models import AbstractUser
from decimal import Decimal
from django.core.exceptions import ValidationError


class User(AbstractUser):
    class Role (models.IntegerChoices):
            MANAGER = 1
            SERVER_HOST = 2
            KITCHEN_STAFF = 3
            DELIVERY_DRIVER = 4
            CUSTOMER = 5
            OWNER = 6

    email = models.EmailField() # field type contains email validation
    role = models.IntegerField(choices=Role.choices) # uses chocies defined in subclass Role
    created_at = models.DateTimeField(auto_now_add=True)

    # === STAFF BUSINESS FIELDS (Michael - Week 4) ===
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    shift_start = models.TimeField(blank=True, null=True)
    shift_end = models.TimeField(blank=True, null=True)
    is_active_staff = models.BooleanField(default=True)

    
    # Adding validation to make sure that the end time and the start time is correct for the shift
    def clean(self):
        if self.shift_start and self.shift_end:
            if self.shift_end <= self.shift_start:
                raise ValidationError('Shift end must be after shift start.')

    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Category(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Restaurant(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True) # allows a MANAGER user to be delieted without deleting a restaurant
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)
    is_active = models.BooleanField(default=True) # Restaurant defaults to active as soon as it's created

    # Adding model level validation to ensure data integrity
    def clean(self):
        if self.opening_time and self.closing_time:
            if self.closing_time <= self.opening_time:
                raise ValidationError('Closing time must be after opening time.')

    def __str__(self):
        return self.name

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # FK exists in OneToOneField here, allows one User to have exactly one Customer record
    phone_number = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    loyalty_points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class StaffInvite(models.Model):
    email = models.EmailField(unique=True)
    role = models.IntegerField(choices=User.Role.choices)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.get_role_display()}"

class Inventory(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE) # if restaurant is deleted, inventory is deleted with it
    ingredient_name = models.CharField(max_length=100)
    current_level = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    last_updated = models.DateTimeField(auto_now=True) # allows filed to save upon update

    def __str__(self):
        return f'{self.ingredient_name} - {self.restaurant}'    


class Table(models.Model):
    class Status (models.IntegerChoices):
        AVAILABLE = 1
        OCCUPIED = 2
        RESERVED = 3
        NEEDS_CLEANING = 4

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE) # if restaurant is deleted so are its tables
    label = models.CharField(max_length=20)
    seats = models.IntegerField()
    grid_squares = models.JSONField()
    status = models.IntegerField(choices=Status.choices, default=Status.AVAILABLE) # as soon as a new table is created, it's made AVAILABLE.  Uses subclass Status as choices

    # ==================== NEW FIELD ====================
    assigned_server = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_tables'
    )
    # ===================================================

    def __str__(self):
        return f'{self.label} - {self.restaurant}'

class TableLayout(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE) # if restaurant is deleted so is its table layout
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    grid_data = models.JSONField()
    uploaded_at = models.DateTimeField(auto_now_add=True)


class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True) # if category is deleted, menuItem is just marked as NULL for this field
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/', null=True, blank=True)

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.restaurant} - {self.menu_item}'

class MenuItemTag(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.menu_item} - {self.tag}'


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

    # Adding validation rule to make sure that the party size is always 1 or more
    def clean(self):
        if self.party_size is not None and self.party_size <= 0:
            raise ValidationError('Party size must be greater than 0.')
    
    def __str__(self):
        return f'Reservation {self.id} - {self.restaurant}'


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
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True)
    # Direct table FK, allows server view to group orders by table without needing a reservation
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    assigned_server = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='served_orders', blank=True)
    assigned_driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='delivered_orders', blank=True)
    order_type = models.IntegerField(choices=OrderType.choices) 
    delivery_address = models.CharField(max_length=255, null=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    loyalty_discount = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0')) # Decimal('0') used instead of 0 to satisfy DecimalField type requirements
    # Tax is calculated as 5% GST on (sub_total: loyalty_discount)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    special_instruction = models.TextField(null=True, blank=True)
    payment_status = models.IntegerField(choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    order_status = models.IntegerField(choices=OrderStatus.choices, default=OrderStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    points_earned = models.IntegerField(default=0)
    points_redeemed = models.IntegerField(default=0)

    def __str__(self):
        return f'Order {self.id} - {self.restaurant}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Order {self.order.id} - {self.menu_item}'


class Payment(models.Model):
    class PaymentMethod (models.IntegerChoices):
        CREDIT_CARD = 1
        MOBILE_WALLET = 2

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    method = models.IntegerField(choices=PaymentMethod.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=255, unique=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    # Tracking failed payments too
    status = models.CharField(max_length=20, default='succeeded')

    def __str__(self):
        return f'Payment {self.transaction_id} - Order {self.order.id}'
    

class PreOrder(models.Model):
    """
    A pre-order is created by a customer when they book a reservation.
    It holds items they want to order before arriving at the restaurant.
    The server activates it once the customer is seated, which converts
    it into a real Order and sends it to the kitchen.
    """
    class Status(models.IntegerChoices):
        PENDING = 1      # customer has added items, not yet activated
        ACTIVATED = 2    # server has activated it, order sent to kitchen
        CANCELLED = 3    # customer cancelled before arrival

    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='preorder'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE
    )
    special_instruction = models.TextField(null=True, blank=True)
    status = models.IntegerField(
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'PreOrder for Reservation {self.reservation.id}'


class PreOrderItem(models.Model):
    """
    An individual item inside a pre-order.
    Mirrors OrderItem but linked to PreOrder instead of Order.
    """
    preorder = models.ForeignKey(
        PreOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.SET_NULL,
        null=True
    )
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'PreOrderItem {self.menu_item} x{self.quantity}'


class TableTransferRequest(models.Model):
    """
    When a server wants to transfer a table to another server,
    this request is created. The receiving server sees a notification
    and can accept or decline. On accept, the table is reassigned.
    On decline, the table stays with the requesting server and
    the requester gets a notification that it was declined.
    """
    class Status(models.IntegerChoices):
        PENDING = 1
        ACCEPTED = 2
        DECLINED = 3

    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name='transfer_requests'
    )
    # the server who currently owns the table and is requesting the transfer
    requesting_server = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='outgoing_transfer_requests'
    )
    # the server who is being asked to take the table
    receiving_server = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='incoming_transfer_requests'
    )
    status = models.IntegerField(
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Transfer request for {self.table.label} from {self.requesting_server} to {self.receiving_server}'


class ManagerNote(models.Model):
    """
    A note created by a manager or owner that appears at the top of
    the targeted role's dashboard. Scoped to a specific restaurant so
    notes from one location do not bleed into another location's staff.
    Notes auto-expire after 24 hours. Manager can edit or delete early.
    Target role of 0 means all staff at this restaurant see it.
    """
    TARGET_ALL = 0

    TARGET_CHOICES = [
        (0, 'All Staff'),
        (User.Role.MANAGER,         'Managers'),
        (User.Role.SERVER_HOST,     'Servers / Hosts'),
        (User.Role.KITCHEN_STAFF,   'Kitchen Staff'),
        (User.Role.DELIVERY_DRIVER, 'Delivery Drivers'),
        (User.Role.OWNER,           'Owners'),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='manager_notes'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    message = models.TextField()
    # target_role of 0 means broadcast to all staff at this restaurant
    target_role = models.IntegerField(choices=TARGET_CHOICES, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # expires_at is set automatically to 24 hours after creation
    expires_at = models.DateTimeField()

    def __str__(self):
        return f'Note by {self.created_by} at {self.restaurant}: {self.message[:40]}'

class Notification(models.Model):
    """
    Notification for server/host when a table's order status changes to READY.
    Linked to the table so server view can show per-table alerts.
    """
    class NotificationType(models.IntegerChoices):
        ORDER_READY = 1
        ORDER_CANCELLED = 2
        TABLE_ATTENTION = 3

    table = models.ForeignKey(Table, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.IntegerField(choices=NotificationType.choices, default=NotificationType.ORDER_READY)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for Order #{self.order.id} - {self.message}'