import pytest
from django.contrib.auth import get_user_model
from restaurant.forms import CustomerSignUpForm, RestaurantForm, StaffSignUpForm, AddStaffForm
from restaurant.models import StaffInvite
from django.utils import timezone

User = get_user_model()


# ====================== RESTAURANT FORM TESTS ======================

# verifies RestaurantForm accepts valid data
@pytest.mark.django_db
def test_restaurant_form_valid():
    form = RestaurantForm(data={
        'name': 'Urban Spark Downtown',
        'address': '123 Main St',
        'phone_number': '403-555-1234',
        'opening_time': '09:00',
        'closing_time': '22:00',
        'latitude': '51.044733',
        'longitude': '-114.0718'
    })
    assert form.is_valid()


# verifies RestaurantForm rejects missing required fields
@pytest.mark.django_db
def test_restaurant_form_missing_name():
    form = RestaurantForm(data={
        'name': '',
        'address': '123 Main St',
        'phone_number': '403-555-1234',
        'opening_time': '09:00',
        'closing_time': '22:00',
        'latitude': '51.044733',
        'longitude': '-114.071883'
    })
    assert not form.is_valid()
    assert 'name' in form.errors


# verifies RestaurantForm rejects invalid latitude
@pytest.mark.django_db
def test_restaurant_form_invalid_latitude():
    form = RestaurantForm(data={
        'name': 'Urban Spark',
        'address': '123 Main St',
        'phone_number': '403-555-1234',
        'opening_time': '09:00',
        'closing_time': '22:00',
        'latitude': 'not_a_number',
        'longitude': '-114.071883'
    })
    assert not form.is_valid()
    assert 'latitude' in form.errors


# ====================== CUSTOMER SIGNUP FORM TESTS ======================

# verifies CustomerSignUpForm accepts valid data
@pytest.mark.django_db
def test_customer_signup_form_valid():
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


# verifies CustomerSignUpForm rejects mismatched passwords
@pytest.mark.django_db
def test_customer_signup_form_password_mismatch():
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


# verifies CustomerSignUpForm rejects missing phone number
@pytest.mark.django_db
def test_customer_signup_form_missing_phone():
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


# verifies CustomerSignUpForm rejects missing address
@pytest.mark.django_db
def test_customer_signup_form_missing_address():
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


# verifies CustomerSignUpForm rejects invalid email format
@pytest.mark.django_db
def test_customer_signup_form_invalid_email():
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


# verifies CustomerSignUpForm rejects duplicate username
@pytest.mark.django_db
def test_customer_signup_form_duplicate_username():
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


# ====================== STAFF SIGNUP FORM TESTS ======================

# verifies StaffSignUpForm accepts valid data
@pytest.mark.django_db
def test_staff_signup_form_valid():
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


# verifies StaffSignUpForm rejects mismatched passwords
@pytest.mark.django_db
def test_staff_signup_form_password_mismatch():
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


# ====================== ADD STAFF FORM TESTS ======================

# verifies AddStaffForm accepts valid data
@pytest.mark.django_db
def test_add_staff_form_valid():
    form = AddStaffForm(data={
        'email': 'newstaff@urbansparkstaff.com',
        'role': 3
    })
    assert form.is_valid()


# verifies AddStaffForm rejects invalid email
@pytest.mark.django_db
def test_add_staff_form_invalid_email():
    form = AddStaffForm(data={
        'email': 'not_an_email',
        'role': 3
    })
    assert not form.is_valid()
    assert 'email' in form.errors


# verifies AddStaffForm rejects missing role
@pytest.mark.django_db
def test_add_staff_form_missing_role():
    form = AddStaffForm(data={
        'email': 'staff@urbansparkstaff.com',
        'role': ''
    })
    assert not form.is_valid()
    assert 'role' in form.errors


# verifies AddStaffForm rejects duplicate email since StaffInvite email is unique
@pytest.mark.django_db
def test_add_staff_form_duplicate_email():
    StaffInvite.objects.create(email='existing@urbansparkstaff.com', role=2)
    form = AddStaffForm(data={
        'email': 'existing@urbansparkstaff.com',
        'role': 3
    })
    assert not form.is_valid()
    assert 'email' in form.errors
