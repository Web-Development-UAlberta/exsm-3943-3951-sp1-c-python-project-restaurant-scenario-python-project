import pytest
from django.contrib.auth import get_user_model
from restaurant.forms import (
    CustomerSignUpForm, CustomerEditForm, RestaurantForm,
    StaffSignUpForm, StaffEditForm, AddStaffForm,
    OrderForm, ReservationForm, InventoryForm
)
from restaurant.models import StaffInvite, Restaurant, Category, Table
from django.utils import timezone
from decimal import Decimal
import datetime

User = get_user_model()


# ====================== RESTAURANT FORM TESTS ======================

@pytest.mark.django_db
def test_restaurant_form_valid():
    # verifies RestaurantForm accepts valid address and time data
    # latitude and longitude are no longer fields since geocoding handles them automatically
    form = RestaurantForm(data={
        'name': 'Urban Spark Downtown',
        'address': '300 Centre St, Calgary, AB',
        'phone_number': '403-555-1234',
        'opening_time': '09:00',
        'closing_time': '22:00',
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_restaurant_form_missing_name():
    # verifies RestaurantForm rejects a form with no restaurant name
    form = RestaurantForm(data={
        'name': '',
        'address': '123 Main St',
        'phone_number': '403-555-1234',
        'opening_time': '09:00',
        'closing_time': '22:00',
    })
    assert not form.is_valid()
    assert 'name' in form.errors


@pytest.mark.django_db
def test_restaurant_form_missing_address():
    # verifies RestaurantForm rejects a form with no address
    form = RestaurantForm(data={
        'name': 'Test Restaurant',
        'address': '',
        'phone_number': '403-555-1234',
        'opening_time': '09:00',
        'closing_time': '22:00',
    })
    assert not form.is_valid()
    assert 'address' in form.errors


@pytest.mark.django_db
def test_restaurant_form_missing_phone():
    # verifies RestaurantForm rejects a form with no phone number
    form = RestaurantForm(data={
        'name': 'Test Restaurant',
        'address': '123 Main St',
        'phone_number': '',
        'opening_time': '09:00',
        'closing_time': '22:00',
    })
    assert not form.is_valid()
    assert 'phone_number' in form.errors


@pytest.mark.django_db
def test_restaurant_form_missing_opening_time():
    # verifies RestaurantForm rejects a form with no opening time
    form = RestaurantForm(data={
        'name': 'Test Restaurant',
        'address': '123 Main St',
        'phone_number': '403-555-1234',
        'opening_time': '',
        'closing_time': '22:00',
    })
    assert not form.is_valid()
    assert 'opening_time' in form.errors


@pytest.mark.django_db
def test_restaurant_form_does_not_have_lat_lng_fields():
    # verifies latitude and longitude are not exposed on the form
    # geocoding handles coordinates automatically in the view
    form = RestaurantForm()
    assert 'latitude' not in form.fields
    assert 'longitude' not in form.fields


# ====================== CUSTOMER SIGNUP FORM TESTS ======================

@pytest.mark.django_db
def test_customer_signup_form_valid():
    # verifies CustomerSignUpForm accepts all required fields with valid data
    form = CustomerSignUpForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'johndoe',
        'email': 'john@example.com',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
        'phone_number': '4035551234',
        'address': '456 Elm Street'
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_customer_signup_form_password_mismatch():
    # verifies CustomerSignUpForm rejects mismatched passwords
    form = CustomerSignUpForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'johndoe2',
        'email': 'john2@example.com',
        'password1': 'TestPass123!',
        'password2': 'WrongPass123!',
        'phone_number': '4035551234',
        'address': '456 Elm Street'
    })
    assert not form.is_valid()
    assert 'password2' in form.errors


@pytest.mark.django_db
def test_customer_signup_form_missing_phone():
    # verifies CustomerSignUpForm rejects a form with no phone number
    form = CustomerSignUpForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'johndoe3',
        'email': 'john3@example.com',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
        'phone_number': '',
        'address': '456 Elm Street'
    })
    assert not form.is_valid()
    assert 'phone_number' in form.errors


@pytest.mark.django_db
def test_customer_signup_form_missing_address():
    # verifies CustomerSignUpForm rejects a form with no address
    form = CustomerSignUpForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'johndoe4',
        'email': 'john4@example.com',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
        'phone_number': '4035551234',
        'address': ''
    })
    assert not form.is_valid()
    assert 'address' in form.errors


@pytest.mark.django_db
def test_customer_signup_form_invalid_email():
    # verifies CustomerSignUpForm rejects a malformed email address
    form = CustomerSignUpForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'johndoe5',
        'email': 'not_an_email',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
        'phone_number': '4035551234',
        'address': '456 Elm Street'
    })
    assert not form.is_valid()
    assert 'email' in form.errors


@pytest.mark.django_db
def test_customer_signup_form_duplicate_username():
    # verifies CustomerSignUpForm rejects a username that already exists
    User.objects.create_user(username='existinguser', password='pass', role=5)
    form = CustomerSignUpForm(data={
        'first_name': 'Jane',
        'last_name': 'Doe',
        'username': 'existinguser',
        'email': 'jane@example.com',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
        'phone_number': '4035559999',
        'address': '789 Oak Ave'
    })
    assert not form.is_valid()
    assert 'username' in form.errors


@pytest.mark.django_db
def test_customer_signup_form_weak_password():
    # verifies CustomerSignUpForm rejects a weak password that does not meet Django requirements
    form = CustomerSignUpForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'weakpassuser',
        'email': 'weak@example.com',
        'password1': '123',
        'password2': '123',
        'phone_number': '4035551234',
        'address': '456 Elm Street'
    })
    assert not form.is_valid()


# ====================== CUSTOMER EDIT FORM TESTS ======================

@pytest.mark.django_db
def test_customer_edit_form_valid():
    # verifies CustomerEditForm accepts valid update data without a password change
    user = User.objects.create_user(
        username='editcustomer', password='TestPass123!', role=User.Role.CUSTOMER
    )
    from restaurant.models import Customer
    customer = Customer.objects.create(
        user=user, phone_number='4031234567', address='123 Test St'
    )
    form = CustomerEditForm(instance=customer, data={
        'first_name': 'Updated',
        'last_name': 'Name',
        'email': 'updated@test.com',
        'phone_number': '4039876543',
        'address': '456 New St',
        'password1': '',
        'password2': ''
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_customer_edit_form_password_mismatch():
    # verifies CustomerEditForm rejects mismatched new passwords
    user = User.objects.create_user(
        username='editpass', password='TestPass123!', role=User.Role.CUSTOMER
    )
    from restaurant.models import Customer
    customer = Customer.objects.create(
        user=user, phone_number='4031234567', address='123 Test St'
    )
    form = CustomerEditForm(instance=customer, data={
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@test.com',
        'phone_number': '4031234567',
        'address': '123 Test St',
        'password1': 'NewPass123!',
        'password2': 'DifferentPass!'
    })
    assert not form.is_valid()


@pytest.mark.django_db
def test_customer_edit_form_password_not_required():
    # verifies CustomerEditForm does not require a password change when left blank
    user = User.objects.create_user(
        username='nopwdchange', password='TestPass123!', role=User.Role.CUSTOMER
    )
    from restaurant.models import Customer
    customer = Customer.objects.create(
        user=user, phone_number='4031234567', address='123 Test St'
    )
    form = CustomerEditForm(instance=customer, data={
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@test.com',
        'phone_number': '4031234567',
        'address': '123 Test St',
        'password1': '',
        'password2': ''
    })
    assert form.is_valid()


# ====================== STAFF SIGNUP FORM TESTS ======================

@pytest.mark.django_db
def test_staff_signup_form_valid():
    # verifies StaffSignUpForm accepts valid registration data
    form = StaffSignUpForm(data={
        'first_name': 'Jane',
        'last_name': 'Smith',
        'username': 'janesmith',
        'email': 'jane@urbansparkstaff.com',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
        'phone_number': '4035559876',
        'address': '789 Oak Ave'
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_staff_signup_form_password_mismatch():
    # verifies StaffSignUpForm rejects mismatched passwords
    form = StaffSignUpForm(data={
        'first_name': 'Jane',
        'last_name': 'Smith',
        'username': 'janesmith2',
        'email': 'jane2@urbansparkstaff.com',
        'password1': 'TestPass123!',
        'password2': 'WrongPass456!',
        'phone_number': '4035559876',
        'address': '789 Oak Ave'
    })
    assert not form.is_valid()
    assert 'password2' in form.errors


@pytest.mark.django_db
def test_staff_signup_form_missing_phone():
    # verifies StaffSignUpForm rejects a form with no phone number
    form = StaffSignUpForm(data={
        'first_name': 'Jane',
        'last_name': 'Smith',
        'username': 'janesmith3',
        'email': 'jane3@urbansparkstaff.com',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
        'phone_number': '',
        'address': '789 Oak Ave'
    })
    assert not form.is_valid()
    assert 'phone_number' in form.errors


# ====================== STAFF EDIT FORM TESTS ======================

@pytest.mark.django_db
def test_staff_edit_form_valid():
    # verifies StaffEditForm accepts valid staff update data including shift times
    form = StaffEditForm(data={
        'first_name': 'Peter',
        'last_name': 'Parker',
        'email': 'peter@urbanspark.com',
        'phone_number': '4031234567',
        'shift_start': '09:00',
        'shift_end': '17:00',
        'is_active_staff': True
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_staff_edit_form_missing_email():
    # verifies StaffEditForm rejects a form with no email address
    form = StaffEditForm(data={
        'first_name': 'Peter',
        'last_name': 'Parker',
        'email': '',
        'phone_number': '4031234567',
        'shift_start': '09:00',
        'shift_end': '17:00',
        'is_active_staff': True
    })
    assert not form.is_valid()
    assert 'email' in form.errors


@pytest.mark.django_db
def test_staff_edit_form_invalid_email():
    # verifies StaffEditForm rejects a malformed email address
    form = StaffEditForm(data={
        'first_name': 'Peter',
        'last_name': 'Parker',
        'email': 'notanemail',
        'phone_number': '4031234567',
        'shift_start': '09:00',
        'shift_end': '17:00',
        'is_active_staff': True
    })
    assert not form.is_valid()
    assert 'email' in form.errors


@pytest.mark.django_db
def test_staff_edit_form_shift_fields_not_required():
    # verifies StaffEditForm is valid without shift times since they are optional
    form = StaffEditForm(data={
        'first_name': 'Peter',
        'last_name': 'Parker',
        'email': 'peter@test.com',
        'phone_number': '',
        'shift_start': '',
        'shift_end': '',
        'is_active_staff': True
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_staff_edit_form_has_is_active_staff_field():
    # verifies the is_active_staff field exists on the staff edit form
    form = StaffEditForm()
    assert 'is_active_staff' in form.fields


@pytest.mark.django_db
def test_staff_edit_form_is_active_staff_label():
    # verifies the is_active_staff field label is correctly set to Staff Active
    form = StaffEditForm()
    assert form.fields['is_active_staff'].label == 'Staff Active'


# ====================== ADD STAFF FORM TESTS ======================

@pytest.mark.django_db
def test_add_staff_form_valid():
    # verifies AddStaffForm accepts a valid email and role combination
    form = AddStaffForm(data={
        'email': 'newstaff@urbansparkstaff.com',
        'role': User.Role.KITCHEN_STAFF
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_add_staff_form_invalid_email():
    # verifies AddStaffForm rejects a malformed email address
    form = AddStaffForm(data={
        'email': 'not_an_email',
        'role': User.Role.KITCHEN_STAFF
    })
    assert not form.is_valid()
    assert 'email' in form.errors


@pytest.mark.django_db
def test_add_staff_form_missing_role():
    # verifies AddStaffForm rejects a form with no role selected
    form = AddStaffForm(data={
        'email': 'staff@urbansparkstaff.com',
        'role': ''
    })
    assert not form.is_valid()
    assert 'role' in form.errors


@pytest.mark.django_db
def test_add_staff_form_duplicate_email():
    # verifies AddStaffForm rejects a duplicate email since StaffInvite email is unique
    StaffInvite.objects.create(email='existing@urbansparkstaff.com', role=User.Role.SERVER_HOST)
    form = AddStaffForm(data={
        'email': 'existing@urbansparkstaff.com',
        'role': User.Role.KITCHEN_STAFF
    })
    assert not form.is_valid()
    assert 'email' in form.errors


@pytest.mark.django_db
def test_add_staff_form_excludes_customer_role():
    # verifies the role dropdown on AddStaffForm does not include the CUSTOMER role
    # customers register through the customer signup page, not staff invites
    form = AddStaffForm()
    role_values = [value for value, label in form.fields['role'].choices]
    assert User.Role.CUSTOMER not in role_values


@pytest.mark.django_db
def test_add_staff_form_includes_all_staff_roles():
    # verifies the role dropdown includes all staff roles except customer
    form = AddStaffForm()
    role_values = [value for value, label in form.fields['role'].choices]
    assert User.Role.MANAGER in role_values
    assert User.Role.SERVER_HOST in role_values
    assert User.Role.KITCHEN_STAFF in role_values
    assert User.Role.DELIVERY_DRIVER in role_values
    assert User.Role.OWNER in role_values


# ====================== ORDER FORM TESTS ======================

@pytest.mark.django_db
def test_order_form_valid_dine_in():
    # verifies OrderForm accepts a valid dine-in order without a delivery address
    form = OrderForm(data={
        'order_type': str(OrderForm.Meta.model.OrderType.DINE_IN),
        'delivery_address': '',
        'special_instruction': '',
        'redeem_points': 'False'
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_order_form_valid_takeout():
    # verifies OrderForm accepts a valid take-out order without a delivery address
    form = OrderForm(data={
        'order_type': str(OrderForm.Meta.model.OrderType.TAKE_OUT),
        'delivery_address': '',
        'special_instruction': 'Extra ketchup',
        'redeem_points': 'False'
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_order_form_delivery_requires_address():
    # verifies OrderForm rejects a delivery order with no delivery address
    form = OrderForm(data={
        'order_type': str(OrderForm.Meta.model.OrderType.DELIVERY),
        'delivery_address': '',
        'special_instruction': '',
        'redeem_points': 'False'
    })
    assert not form.is_valid()


@pytest.mark.django_db
def test_order_form_delivery_with_address_is_valid():
    # verifies OrderForm accepts a delivery order when an address is provided
    form = OrderForm(data={
        'order_type': str(OrderForm.Meta.model.OrderType.DELIVERY),
        'delivery_address': '100 Main St, Calgary, AB',
        'special_instruction': '',
        'redeem_points': 'False'
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_order_form_redeem_points_choices():
    # verifies the redeem_points field has exactly two choices: True and False
    form = OrderForm()
    choices = [str(v) for v, l in form.fields['redeem_points'].choices]
    assert 'True' in choices or True in form.fields['redeem_points'].choices
    assert len(form.fields['redeem_points'].choices) == 2


# ====================== RESERVATION FORM TESTS ======================

@pytest.mark.django_db
def test_reservation_form_valid_for_logged_in_customer():
    # verifies ReservationForm is valid for a logged-in customer
    # guest fields are hidden and not required when a customer user is passed
    restaurant = Restaurant.objects.create(
        name='Test', address='Addr', phone_number='123',
        opening_time=datetime.time(9, 0), closing_time=datetime.time(22, 0),
        latitude=Decimal('51.0'), longitude=Decimal('-114.0'), is_active=True
    )
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    user = User.objects.create_user(
        username='resvcustomer', password='TestPass123!', role=User.Role.CUSTOMER
    )
    reservation_time = timezone.now().replace(
        hour=15, minute=0, second=0, microsecond=0
    ) + timezone.timedelta(days=1)
    form = ReservationForm(user=user, data={
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': reservation_time.strftime('%Y-%m-%dT%H:%M'),
        'party_size': 2,
        'guest_name': '',
        'guest_email': '',
        'guest_phone_number': ''
    })
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_reservation_form_guest_requires_contact_info():
    # verifies ReservationForm requires guest contact info when no user is passed
    restaurant = Restaurant.objects.create(
        name='Test', address='Addr', phone_number='123',
        opening_time=datetime.time(9, 0), closing_time=datetime.time(22, 0),
        latitude=Decimal('51.0'), longitude=Decimal('-114.0'), is_active=True
    )
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    reservation_time = timezone.now().replace(
        hour=15, minute=0, second=0, microsecond=0
    ) + timezone.timedelta(days=1)
    form = ReservationForm(user=None, data={
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': reservation_time.strftime('%Y-%m-%dT%H:%M'),
        'party_size': 2,
        'guest_name': '',
        'guest_email': '',
        'guest_phone_number': ''
    })
    assert not form.is_valid()


@pytest.mark.django_db
def test_reservation_form_rejects_past_datetime():
    # verifies ReservationForm rejects a reservation time in the past
    restaurant = Restaurant.objects.create(
        name='Test', address='Addr', phone_number='123',
        opening_time=datetime.time(9, 0), closing_time=datetime.time(22, 0),
        latitude=Decimal('51.0'), longitude=Decimal('-114.0'), is_active=True
    )
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    user = User.objects.create_user(
        username='pastresv', password='TestPass123!', role=User.Role.CUSTOMER
    )
    form = ReservationForm(user=user, data={
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': '2020-01-01T12:00',
        'party_size': 2,
        'guest_name': '',
        'guest_email': '',
        'guest_phone_number': ''
    })
    assert not form.is_valid()


@pytest.mark.django_db
def test_reservation_form_rejects_oversized_party():
    # verifies ReservationForm rejects a party size above 20
    restaurant = Restaurant.objects.create(
        name='Test', address='Addr', phone_number='123',
        opening_time=datetime.time(9, 0), closing_time=datetime.time(22, 0),
        latitude=Decimal('51.0'), longitude=Decimal('-114.0'), is_active=True
    )
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    user = User.objects.create_user(
        username='bigparty', password='TestPass123!', role=User.Role.CUSTOMER
    )
    reservation_time = timezone.now().replace(
        hour=15, minute=0, second=0, microsecond=0
    ) + timezone.timedelta(days=1)
    form = ReservationForm(user=user, data={
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': reservation_time.strftime('%Y-%m-%dT%H:%M'),
        'party_size': 25,
        'guest_name': '',
        'guest_email': '',
        'guest_phone_number': ''
    })
    assert not form.is_valid()


@pytest.mark.django_db
def test_reservation_form_rejects_party_larger_than_table():
    # verifies ReservationForm rejects a party size larger than the table can seat
    restaurant = Restaurant.objects.create(
        name='Test', address='Addr', phone_number='123',
        opening_time=datetime.time(9, 0), closing_time=datetime.time(22, 0),
        latitude=Decimal('51.0'), longitude=Decimal('-114.0'), is_active=True
    )
    table = Table.objects.create(
        label='T1', seats=2, grid_squares={}, restaurant=restaurant
    )
    user = User.objects.create_user(
        username='toobigtable', password='TestPass123!', role=User.Role.CUSTOMER
    )
    reservation_time = timezone.now().replace(
        hour=15, minute=0, second=0, microsecond=0
    ) + timezone.timedelta(days=1)
    form = ReservationForm(user=user, data={
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': reservation_time.strftime('%Y-%m-%dT%H:%M'),
        'party_size': 5,
        'guest_name': '',
        'guest_email': '',
        'guest_phone_number': ''
    })
    assert not form.is_valid()


@pytest.mark.django_db
def test_reservation_form_hides_guest_fields_for_logged_in_customer():
    # verifies the guest name, email, and phone fields are hidden for logged-in customers
    user = User.objects.create_user(
        username='hideguest', password='TestPass123!', role=User.Role.CUSTOMER
    )
    form = ReservationForm(user=user)
    from django.forms import HiddenInput
    assert isinstance(form.fields['guest_name'].widget, HiddenInput)
    assert isinstance(form.fields['guest_email'].widget, HiddenInput)
    assert isinstance(form.fields['guest_phone_number'].widget, HiddenInput)


@pytest.mark.django_db
def test_reservation_form_shows_guest_fields_for_anonymous():
    # verifies the guest contact fields are visible and required when no user is passed
    form = ReservationForm(user=None)
    from django.forms import HiddenInput
    assert not isinstance(form.fields['guest_name'].widget, HiddenInput)
    assert form.fields['guest_name'].required is True


# ====================== INVENTORY FORM TESTS ======================

@pytest.mark.django_db
def test_inventory_form_valid():
    # verifies InventoryForm accepts valid ingredient data
    form = InventoryForm(data={
        'ingredient_name': 'Beef Patties',
        'current_level': '50.00',
        'unit': 'kg',
        'reorder_level': '10.00'
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_inventory_form_missing_ingredient_name():
    # verifies InventoryForm rejects a form with no ingredient name
    form = InventoryForm(data={
        'ingredient_name': '',
        'current_level': '50.00',
        'unit': 'kg',
        'reorder_level': '10.00'
    })
    assert not form.is_valid()
    assert 'ingredient_name' in form.errors


@pytest.mark.django_db
def test_inventory_form_missing_current_level():
    # verifies InventoryForm rejects a form with no current stock level
    form = InventoryForm(data={
        'ingredient_name': 'Tomatoes',
        'current_level': '',
        'unit': 'kg',
        'reorder_level': '5.00'
    })
    assert not form.is_valid()
    assert 'current_level' in form.errors


@pytest.mark.django_db
def test_inventory_form_missing_unit():
    # verifies InventoryForm rejects a form with no unit of measurement
    form = InventoryForm(data={
        'ingredient_name': 'Cheese',
        'current_level': '20.00',
        'unit': '',
        'reorder_level': '5.00'
    })
    assert not form.is_valid()
    assert 'unit' in form.errors


@pytest.mark.django_db
def test_inventory_form_non_numeric_current_level():
    # verifies InventoryForm rejects a non-numeric current level value
    form = InventoryForm(data={
        'ingredient_name': 'Potatoes',
        'current_level': 'lots',
        'unit': 'kg',
        'reorder_level': '10.00'
    })
    assert not form.is_valid()
    assert 'current_level' in form.errors


@pytest.mark.django_db
def test_inventory_form_has_styled_widgets():
    # verifies the InventoryForm fields use the form-input CSS class for consistent styling
    form = InventoryForm()
    assert form.fields['ingredient_name'].widget.attrs.get('class') == 'form-input'
    assert form.fields['current_level'].widget.attrs.get('class') == 'form-input'
    assert form.fields['unit'].widget.attrs.get('class') == 'form-input'
    assert form.fields['reorder_level'].widget.attrs.get('class') == 'form-input'