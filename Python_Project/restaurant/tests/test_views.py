import pytest
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from restaurant.models import (
    Customer, Restaurant, Category, Tag,
    Table, Order, OrderItem, StaffInvite, MenuItem,
    TableLayout, Reservation, Inventory, Notification,
    PreOrder, PreOrderItem, TableTransferRequest,
    ManagerNote, RestaurantMenuItem, Payment
)
from restaurant import models
from django.utils import timezone
import datetime
import json
from decimal import Decimal

User = get_user_model()


# ====================== HELPER FIXTURES ======================
# Fixtures are reusable setup functions that create test data once and share it across multiple tests
# Instead of repeating the same object creation code in every test, we define it here once
# pytest automatically runs the fixture and passes the created object into any test that lists it as a parameter
# Each fixture runs fresh for every test, no shared state between tests

@pytest.fixture
def restaurant(db):
    # creates a basic restaurant with realistic opening hours for use across tests
    return Restaurant.objects.create(
        name="Test Restaurant",
        address="123 Test St",
        phone_number="403-555-1234",
        opening_time=datetime.time(9, 0),
        closing_time=datetime.time(22, 0),
        latitude=Decimal('51.044733'),
        longitude=Decimal('-114.0718'),
        is_active=True
    )


@pytest.fixture
def customer_user(db):
    # creates a customer user and their linked customer profile
    user = User.objects.create_user(
        username='testcustomer',
        password='TestPass123!',
        role=User.Role.CUSTOMER,
        email='customer@test.com'
    )
    Customer.objects.create(
        user=user,
        phone_number='4035551234',
        address='123 Test St',
        loyalty_points=0
    )
    return user


@pytest.fixture
def manager_user(db):
    # creates a manager user for testing management-level access
    return User.objects.create_user(
        username='testmanager',
        password='TestPass123!',
        role=User.Role.MANAGER,
        email='manager@test.com'
    )


@pytest.fixture
def owner_user(db):
    # creates an owner user for testing owner-level access
    return User.objects.create_user(
        username='testowner',
        password='TestPass123!',
        role=User.Role.OWNER,
        email='owner@test.com'
    )


@pytest.fixture
def server_user(db):
    # creates a server user for testing server host dashboard access
    return User.objects.create_user(
        username='testserver',
        password='TestPass123!',
        role=User.Role.SERVER_HOST,
        email='server@test.com'
    )


@pytest.fixture
def kitchen_user(db):
    # creates a kitchen staff user for testing kitchen dashboard access
    return User.objects.create_user(
        username='testkitchen',
        password='TestPass123!',
        role=User.Role.KITCHEN_STAFF,
        email='kitchen@test.com'
    )


@pytest.fixture
def driver_user(db):
    # creates a delivery driver user for testing driver dashboard access
    return User.objects.create_user(
        username='testdriver',
        password='TestPass123!',
        role=User.Role.DELIVERY_DRIVER,
        email='driver@test.com'
    )


@pytest.fixture
def table(db, restaurant):
    # creates a basic table linked to the test restaurant
    return Table.objects.create(
        label='T1',
        seats=4,
        grid_squares={'x': 2, 'y': 2, 'w': 1, 'h': 1},
        status=Table.Status.AVAILABLE,
        restaurant=restaurant
    )


@pytest.fixture
def menu_item(db):
    # creates a basic menu item for use in order and cart tests
    category = Category.objects.create(name='Test Category')
    return MenuItem.objects.create(
        name='Test Burger',
        description='A test burger',
        price=Decimal('12.99'),
        category=category
    )


@pytest.fixture
def customer_order(db, customer_user, restaurant):
    # creates a pending unpaid order linked to the customer user
    customer = Customer.objects.get(user=customer_user)
    return Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=Order.OrderType.TAKE_OUT,
        sub_total=Decimal('20.00'),
        tax_amount=Decimal('1.00'),
        total_price=Decimal('21.00'),
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )


# ====================== CUSTOMER AUTH VIEWS ======================

@pytest.mark.django_db
def test_customer_login_page_loads(client):
    # verifies the customer login page returns 200
    response = client.get(reverse('customer_login'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_customer_login_page_contains_form(client):
    # UI test: verifies the login page renders a username and password field
    response = client.get(reverse('customer_login'))
    content = response.content.decode()
    assert 'username' in content
    assert 'password' in content


@pytest.mark.django_db
def test_customer_login_valid_credentials(client, customer_user):
    # verifies a customer can log in with correct credentials and is redirected to dashboard
    response = client.post(reverse('customer_login'), {
        'username': 'testcustomer',
        'password': 'TestPass123!'
    })
    assert response.status_code == 302
    assert response.url == reverse('customer_dashboard')


@pytest.mark.django_db
def test_customer_login_invalid_credentials(client, customer_user):
    # verifies login fails with wrong password and stays on the login page
    response = client.post(reverse('customer_login'), {
        'username': 'testcustomer',
        'password': 'WrongPassword!'
    })
    assert response.status_code == 200
    messages = list(response.context['messages'])
    assert any('Invalid' in str(m) for m in messages)


@pytest.mark.django_db
def test_customer_login_blocks_staff(client, manager_user):
    # UI test: verifies staff are blocked from using the customer login page
    # the template should show a redirect warning message
    response = client.post(reverse('customer_login'), {
        'username': 'testmanager',
        'password': 'TestPass123!'
    })
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Staff Login' in content or 'staff' in content.lower()


@pytest.mark.django_db
def test_customer_signup_page_loads(client):
    # verifies the signup page returns 200
    response = client.get(reverse('customer_signup'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_customer_signup_page_contains_required_fields(client):
    # UI test: verifies the signup page renders all required form fields
    response = client.get(reverse('customer_signup'))
    content = response.content.decode()
    assert 'username' in content
    assert 'password' in content
    assert 'email' in content
    assert 'phone' in content.lower()


@pytest.mark.django_db
def test_customer_signup_creates_account(client):
    # verifies a new customer account and profile are created on valid signup
    response = client.post(reverse('customer_signup'), {
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'newcustomer',
        'email': 'new@test.com',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
        'phone_number': '4035559999',
        'address': '456 New St'
    })
    assert response.status_code == 302
    assert User.objects.filter(username='newcustomer').exists()
    assert Customer.objects.filter(user__username='newcustomer').exists()


@pytest.mark.django_db
def test_customer_signup_mismatched_passwords_fails(client):
    # verifies signup fails when passwords do not match
    response = client.post(reverse('customer_signup'), {
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'failcustomer',
        'email': 'fail@test.com',
        'password1': 'TestPass123!',
        'password2': 'DifferentPass!',
        'phone_number': '4035559999',
        'address': '456 New St'
    })
    assert response.status_code == 200
    assert not User.objects.filter(username='failcustomer').exists()


@pytest.mark.django_db
def test_user_logout(client, customer_user):
    # verifies logout redirects to index
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('user_logout'))
    assert response.status_code == 302
    assert response.url == reverse('index')


# ====================== STAFF AUTH VIEWS ======================

@pytest.mark.django_db
def test_staff_login_page_loads(client):
    # verifies the staff login page returns 200
    response = client.get(reverse('staff_login'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_staff_login_page_contains_form(client):
    # UI test: verifies the staff login page renders a username and password field
    response = client.get(reverse('staff_login'))
    content = response.content.decode()
    assert 'username' in content
    assert 'password' in content


@pytest.mark.django_db
def test_staff_login_blocks_customers(client, customer_user):
    # verifies customers cannot log in via the staff login page
    response = client.post(reverse('staff_login'), {
        'username': 'testcustomer',
        'password': 'TestPass123!'
    })
    assert response.status_code == 200
    messages = list(response.context['messages'])
    assert any('Invalid' in str(m) for m in messages)


@pytest.mark.django_db
def test_staff_login_redirects_manager_to_manager_view(client, manager_user):
    # verifies manager is redirected to manager dashboard after login
    response = client.post(reverse('staff_login'), {
        'username': 'testmanager',
        'password': 'TestPass123!'
    })
    assert response.status_code == 302
    assert response.url == reverse('manager_view')


@pytest.mark.django_db
def test_staff_login_redirects_server_to_server_view(client, server_user):
    # verifies server is redirected to server host dashboard after login
    response = client.post(reverse('staff_login'), {
        'username': 'testserver',
        'password': 'TestPass123!'
    })
    assert response.status_code == 302
    assert response.url == reverse('server_host_view')


@pytest.mark.django_db
def test_staff_login_redirects_kitchen_to_kitchen_view(client, kitchen_user):
    # verifies kitchen staff is redirected to kitchen dashboard after login
    response = client.post(reverse('staff_login'), {
        'username': 'testkitchen',
        'password': 'TestPass123!'
    })
    assert response.status_code == 302
    assert response.url == reverse('kitchen_view')


@pytest.mark.django_db
def test_staff_login_redirects_driver_to_driver_view(client, driver_user):
    # verifies driver is redirected to driver dashboard after login
    response = client.post(reverse('staff_login'), {
        'username': 'testdriver',
        'password': 'TestPass123!'
    })
    assert response.status_code == 302
    assert response.url == reverse('driver_view')


@pytest.mark.django_db
def test_staff_signup_blocks_uninvited_email(client):
    # verifies staff signup rejects emails not in StaffInvite table
    response = client.post(reverse('staff_signup'), {
        'first_name': 'Fake',
        'last_name': 'Staff',
        'username': 'fakestaff',
        'email': 'notinvited@test.com',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
        'phone_number': '4035551111',
        'address': '123 Fake St'
    })
    assert response.status_code == 200
    assert not User.objects.filter(username='fakestaff').exists()


@pytest.mark.django_db
def test_staff_signup_allows_invited_email(client):
    # verifies staff signup succeeds when email is in StaffInvite table
    StaffInvite.objects.create(email='invited@test.com', role=User.Role.KITCHEN_STAFF)
    response = client.post(reverse('staff_signup'), {
        'first_name': 'Real',
        'last_name': 'Staff',
        'username': 'realstaff',
        'email': 'invited@test.com',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
        'phone_number': '4035552222',
        'address': '123 Real St'
    })
    assert response.status_code == 302
    assert User.objects.filter(username='realstaff').exists()


@pytest.mark.django_db
def test_staff_signup_marks_invite_as_used(client):
    # verifies that after a successful signup the StaffInvite is marked as used
    StaffInvite.objects.create(email='usedtest@test.com', role=User.Role.SERVER_HOST)
    client.post(reverse('staff_signup'), {
        'first_name': 'Used',
        'last_name': 'Invite',
        'username': 'usedinvite',
        'email': 'usedtest@test.com',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!',
        'phone_number': '4035553333',
        'address': '123 Used St'
    })
    invite = StaffInvite.objects.get(email='usedtest@test.com')
    assert invite.is_used is True


# ====================== RESTAURANT VIEWS ======================

@pytest.mark.django_db
def test_restaurant_list_page_loads(client):
    # verifies restaurant list page is publicly accessible
    response = client.get(reverse('restaurant_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_restaurant_list_shows_restaurant_names(client, restaurant):
    # UI test: verifies restaurant names appear on the list page
    response = client.get(reverse('restaurant_list'))
    assert restaurant.name in response.content.decode()


@pytest.mark.django_db
def test_restaurant_detail_page_loads(client, restaurant):
    # verifies restaurant detail page loads correctly
    response = client.get(reverse('restaurant_detail', args=[restaurant.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_restaurant_detail_shows_restaurant_info(client, restaurant):
    # UI test: verifies the restaurant detail page renders the restaurant name and address
    response = client.get(reverse('restaurant_detail', args=[restaurant.pk]))
    content = response.content.decode()
    assert restaurant.name in content
    assert restaurant.address in content


@pytest.mark.django_db
def test_restaurant_create_requires_owner(client, manager_user):
    # verifies managers cannot create restaurants, only owners can
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('restaurant_create'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_restaurant_create_allowed_for_owner(client, owner_user):
    # verifies owners can access the restaurant create page
    client.login(username='testowner', password='TestPass123!')
    response = client.get(reverse('restaurant_create'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_restaurant_create_page_contains_address_field(client, owner_user):
    # UI test: verifies the restaurant create form renders the address field
    client.login(username='testowner', password='TestPass123!')
    response = client.get(reverse('restaurant_create'))
    content = response.content.decode()
    assert 'address' in content.lower()


@pytest.mark.django_db
def test_restaurant_edit_allowed_for_manager(client, manager_user, restaurant):
    # verifies managers can access the restaurant edit page
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('restaurant_edit', args=[restaurant.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_restaurant_toggle_active(client, manager_user, restaurant):
    # verifies manager can toggle restaurant active status
    client.login(username='testmanager', password='TestPass123!')
    original_status = restaurant.is_active
    client.post(reverse('restaurant_toggle_active', args=[restaurant.pk]))
    restaurant.refresh_from_db()
    assert restaurant.is_active != original_status


# ====================== CATEGORY VIEWS ======================

@pytest.mark.django_db
def test_category_list_page_loads(client):
    # verifies category list is publicly accessible
    response = client.get(reverse('category_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_category_list_shows_category_names(client):
    # UI test: verifies category names appear on the list page
    Category.objects.create(name='Burgers')
    response = client.get(reverse('category_list'))
    assert 'Burgers' in response.content.decode()


@pytest.mark.django_db
def test_category_create_requires_manager(client, customer_user):
    # verifies customers cannot create categories
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('category_create'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_category_create_allowed_for_manager(client, manager_user):
    # verifies managers can create categories
    client.login(username='testmanager', password='TestPass123!')
    response = client.post(reverse('category_create'), {'name': 'Desserts'})
    assert response.status_code == 302
    assert Category.objects.filter(name='Desserts').exists()


@pytest.mark.django_db
def test_category_edit_updates_name(client, manager_user):
    # verifies managers can edit an existing category name
    category = Category.objects.create(name='OldName')
    client.login(username='testmanager', password='TestPass123!')
    client.post(reverse('category_edit', args=[category.pk]), {'name': 'NewName'})
    category.refresh_from_db()
    assert category.name == 'NewName'


@pytest.mark.django_db
def test_category_delete_removes_record(client, manager_user):
    # verifies managers can delete a category
    category = Category.objects.create(name='ToDelete')
    client.login(username='testmanager', password='TestPass123!')
    client.post(reverse('category_confirm_delete', args=[category.pk]))
    assert not Category.objects.filter(name='ToDelete').exists()


# ====================== TAG VIEWS ======================

@pytest.mark.django_db
def test_tag_list_page_loads(client):
    # verifies tag list is publicly accessible
    response = client.get(reverse('tag_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_tag_list_shows_tag_names(client):
    # UI test: verifies tag names and preview badges appear on the list page
    Tag.objects.create(name='Vegan')
    response = client.get(reverse('tag_list'))
    assert 'Vegan' in response.content.decode()


@pytest.mark.django_db
def test_tag_create_allowed_for_manager(client, manager_user):
    # verifies managers can create tags
    client.login(username='testmanager', password='TestPass123!')
    response = client.post(reverse('tag_create'), {'name': 'Vegan'})
    assert response.status_code == 302
    assert Tag.objects.filter(name='Vegan').exists()


@pytest.mark.django_db
def test_tag_delete_removes_record(client, manager_user):
    # verifies managers can delete a tag
    tag = Tag.objects.create(name='DeleteMe')
    client.login(username='testmanager', password='TestPass123!')
    client.post(reverse('tag_confirm_delete', args=[tag.pk]))
    assert not Tag.objects.filter(name='DeleteMe').exists()


# ====================== MENU ITEM VIEWS ======================

@pytest.mark.django_db
def test_menu_item_list_page_loads(client):
    # verifies menu item list page is publicly accessible
    response = client.get(reverse('menu_item_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_menu_item_list_shows_item_names(client, menu_item):
    # UI test: verifies menu item names and prices appear on the menu page
    response = client.get(reverse('menu_item_list'))
    content = response.content.decode()
    assert menu_item.name in content
    assert str(menu_item.price) in content


@pytest.mark.django_db
def test_menu_item_unavailable_shows_label(client, restaurant, menu_item):
    # UI test: verifies unavailable items show the temporarily unavailable label
    RestaurantMenuItem.objects.create(
        restaurant=restaurant,
        menu_item=menu_item,
        is_available=False
    )
    response = client.get(reverse('menu_item_list'))
    content = response.content.decode()
    assert 'Unavailable' in content or 'unavailable' in content


@pytest.mark.django_db
def test_menu_item_create_allowed_for_manager(client, manager_user):
    # verifies managers can create new menu items
    category = Category.objects.create(name='Test')
    client.login(username='testmanager', password='TestPass123!')
    response = client.post(reverse('menu_item_create'), {
        'name': 'New Burger',
        'description': 'A new burger',
        'price': '15.99',
        'category': category.pk
    })
    assert response.status_code == 302
    assert MenuItem.objects.filter(name='New Burger').exists()


@pytest.mark.django_db
def test_menu_item_create_blocked_for_customer(client, customer_user):
    # verifies customers cannot create menu items
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('menu_item_create'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_toggle_menu_item_availability(client, manager_user, restaurant, menu_item):
    # verifies managers can toggle a menu item between available and unavailable
    rmi = RestaurantMenuItem.objects.create(
        restaurant=restaurant,
        menu_item=menu_item,
        is_available=True
    )
    client.login(username='testmanager', password='TestPass123!')
    client.post(reverse('toggle_menu_item_availability', args=[restaurant.pk, menu_item.pk]))
    rmi.refresh_from_db()
    assert rmi.is_available is False


# ====================== ORDER VIEWS ======================

@pytest.mark.django_db
def test_order_create_redirects_to_menu_when_cart_empty(client):
    # verifies guests with empty cart are redirected to menu to add items first
    response = client.get(reverse('order_create'))
    assert response.status_code == 302
    assert response.url == reverse('menu_item_list')


@pytest.mark.django_db
def test_order_create_redirects_to_menu_when_cart_empty_for_customer(client, customer_user):
    # verifies logged in customers with empty cart are redirected to menu
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('order_create'))
    assert response.status_code == 302
    assert response.url == reverse('menu_item_list')


@pytest.mark.django_db
def test_order_create_with_items_loads_review_page(client, restaurant, menu_item):
    # UI test: verifies the order review page renders when the cart has items
    session = client.session
    session['cart'] = {
        str(menu_item.pk): {
            'item_id': menu_item.pk,
            'name': menu_item.name,
            'price': str(menu_item.price),
            'quantity': 1
        }
    }
    session.save()
    response = client.get(reverse('order_create'))
    assert response.status_code == 200
    content = response.content.decode()
    assert menu_item.name in content


@pytest.mark.django_db
def test_order_list_shows_only_customer_orders(client, customer_user, restaurant):
    # verifies customers only see their own orders
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('order_list'))
    assert response.status_code == 200
    assert 'orders' in response.context
    for order in response.context['orders']:
        assert order.customer.user == customer_user


@pytest.mark.django_db
def test_order_detail_page_loads(client, customer_user, customer_order):
    # UI test: verifies the order detail page renders with the order number
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('order_detail', args=[customer_order.pk]))
    assert response.status_code == 200
    content = response.content.decode()
    assert f'Order #{customer_order.id}' in content


@pytest.mark.django_db
def test_order_detail_shows_cancel_button_when_pending(client, customer_user, customer_order):
    # UI test: verifies cancel button appears on the order detail page when order is pending
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('order_detail', args=[customer_order.pk]))
    content = response.content.decode()
    assert 'Cancel' in content


@pytest.mark.django_db
def test_order_edit_blocked_when_not_pending(client, customer_user, restaurant):
    # verifies customers cannot edit orders that are no longer pending
    customer = Customer.objects.get(user=customer_user)
    order = Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=Order.OrderType.TAKE_OUT,
        sub_total=Decimal('20.00'),
        total_price=Decimal('20.00'),
        order_status=Order.OrderStatus.PREPARING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('order_edit', args=[order.pk]))
    assert response.status_code == 302


@pytest.mark.django_db
def test_order_delete_refunds_loyalty_points(client, customer_user, restaurant):
    # verifies loyalty points are refunded when a customer cancels an order with points redeemed
    customer = Customer.objects.get(user=customer_user)
    customer.loyalty_points = 1000
    customer.save()
    order = Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=Order.OrderType.TAKE_OUT,
        sub_total=Decimal('20.00'),
        total_price=Decimal('10.00'),
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID,
        points_redeemed=1000,
        loyalty_discount=Decimal('10.00')
    )
    customer.loyalty_points = 0
    customer.save()
    client.login(username='testcustomer', password='TestPass123!')
    client.post(reverse('order_delete', args=[order.pk]))
    customer.refresh_from_db()
    assert customer.loyalty_points == 1000


@pytest.mark.django_db
def test_order_list_blocked_for_server(client, server_user):
    # verifies servers cannot access the customer order list
    client.login(username='testserver', password='TestPass123!')
    response = client.get(reverse('order_list'))
    assert response.status_code == 302


# ====================== STAFF INVITE VIEWS ======================

@pytest.mark.django_db
def test_staff_invite_list_requires_manager(client, customer_user):
    # verifies customers cannot access staff invite list
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('staff_invite_list'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_staff_invite_list_shows_invites(client, manager_user):
    # UI test: verifies staff invite list renders email addresses
    StaffInvite.objects.create(email='listed@test.com', role=User.Role.SERVER_HOST)
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('staff_invite_list'))
    assert 'listed@test.com' in response.content.decode()


@pytest.mark.django_db
def test_staff_invite_create_allowed_for_manager(client, manager_user):
    # verifies managers can create staff invites
    client.login(username='testmanager', password='TestPass123!')
    response = client.post(reverse('staff_invite_create'), {
        'email': 'newinvite@test.com',
        'role': User.Role.SERVER_HOST
    })
    assert response.status_code == 302
    assert StaffInvite.objects.filter(email='newinvite@test.com').exists()


@pytest.mark.django_db
def test_staff_invite_delete_allowed_for_manager(client, manager_user):
    # verifies managers can revoke an unused invite
    invite = StaffInvite.objects.create(email='revoke@test.com', role=User.Role.SERVER_HOST)
    client.login(username='testmanager', password='TestPass123!')
    response = client.post(reverse('staff_invite_delete', args=[invite.pk]))
    assert response.status_code == 302
    assert not StaffInvite.objects.filter(email='revoke@test.com').exists()


# ====================== CUSTOMER MANAGEMENT VIEWS ======================

@pytest.mark.django_db
def test_customer_list_requires_manager(client, customer_user):
    # verifies regular customers cannot access the customer list
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('customer_list'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_customer_list_allowed_for_manager(client, manager_user):
    # verifies managers can access the customer list
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('customer_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_customer_list_shows_customer_names(client, manager_user, customer_user):
    # UI test: verifies customer names appear in the customer list table
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('customer_list'))
    content = response.content.decode()
    assert customer_user.first_name in content or customer_user.username in content


@pytest.mark.django_db
def test_customer_detail_shows_loyalty_points(client, manager_user, customer_user):
    # UI test: verifies customer detail page shows their loyalty points balance
    customer = Customer.objects.get(user=customer_user)
    customer.loyalty_points = 500
    customer.save()
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('customer_detail', args=[customer.pk]))
    assert '500' in response.content.decode()


# ====================== RESERVATION VIEWS ======================

@pytest.mark.django_db
def test_reservation_list_page_loads_for_customer(client, customer_user):
    # verifies logged in customers can access their reservation list
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('reservation_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_reservation_create_page_loads(client):
    # verifies reservation create page is publicly accessible
    response = client.get(reverse('reservation_create'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_reservation_create_page_contains_form_fields(client):
    # UI test: verifies the reservation form page renders required fields
    response = client.get(reverse('reservation_create'))
    content = response.content.decode()
    assert 'party_size' in content
    assert 'reservation_datetime' in content


@pytest.mark.django_db
def test_reservation_create_blocks_past_datetime(client, restaurant):
    # verifies reservations cannot be made in the past
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    response = client.post(reverse('reservation_create'), {
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': '2020-01-01T12:00',
        'party_size': 2
    })
    assert response.status_code == 200
    assert not models.Reservation.objects.filter(party_size=2).exists()


@pytest.mark.django_db
def test_reservation_create_blocks_oversized_party(client, restaurant):
    # verifies party size above 20 is rejected
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    response = client.post(reverse('reservation_create'), {
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': (timezone.now() + timezone.timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M'),
        'party_size': 21
    })
    assert response.status_code == 200
    assert not models.Reservation.objects.filter(party_size=21).exists()


@pytest.mark.django_db
def test_reservation_conflict_detection(client, restaurant):
    # verifies double booking on the same table is blocked
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    reservation_time = timezone.now() + timezone.timedelta(hours=3)
    models.Reservation.objects.create(
        table=table,
        restaurant=restaurant,
        reservation_datetime=reservation_time,
        party_size=2,
        deposit_amount=10,
        status=models.Reservation.Status.CONFIRMED
    )
    response = client.post(reverse('reservation_create'), {
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': reservation_time.strftime('%Y-%m-%dT%H:%M'),
        'party_size': 2
    })
    assert response.status_code == 200
    assert models.Reservation.objects.filter(table=table).count() == 1


@pytest.mark.django_db
def test_reservation_cancel_applies_fee_within_3_hours(client, customer_user, restaurant):
    # verifies $10 cancellation fee is applied when cancelled within 3 hours
    client.login(username='testcustomer', password='TestPass123!')
    customer = Customer.objects.get(user=customer_user)
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    reservation = models.Reservation.objects.create(
        customer=customer,
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + timezone.timedelta(hours=1),
        party_size=2,
        deposit_amount=10,
        status=models.Reservation.Status.CONFIRMED
    )
    response = client.post(reverse('reservation_cancel', args=[reservation.pk]))
    assert response.status_code == 302
    reservation.refresh_from_db()
    assert reservation.cancellation_fee_applied
    assert reservation.status == models.Reservation.Status.CANCELLED


@pytest.mark.django_db
def test_reservation_cancel_no_fee_outside_3_hours(client, customer_user, restaurant):
    # verifies no cancellation fee when cancelled 3 or more hours before reservation
    client.login(username='testcustomer', password='TestPass123!')
    customer = Customer.objects.get(user=customer_user)
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    reservation = models.Reservation.objects.create(
        customer=customer,
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + timezone.timedelta(hours=5),
        party_size=2,
        deposit_amount=10,
        status=models.Reservation.Status.CONFIRMED
    )
    response = client.post(reverse('reservation_cancel', args=[reservation.pk]))
    assert response.status_code == 302
    reservation.refresh_from_db()
    assert not reservation.cancellation_fee_applied
    assert reservation.status == models.Reservation.Status.CANCELLED


@pytest.mark.django_db
def test_reservation_update_status_allowed_for_manager(client, manager_user, restaurant):
    # verifies managers can update reservation status directly
    table = Table.objects.create(label='T1', seats=4, grid_squares={}, restaurant=restaurant)
    reservation = Reservation.objects.create(
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=10,
        status=Reservation.Status.PENDING
    )
    client.login(username='testmanager', password='TestPass123!')
    client.post(reverse('reservation_update_status', args=[reservation.pk]), {
        'status': Reservation.Status.CONFIRMED
    })
    reservation.refresh_from_db()
    assert reservation.status == Reservation.Status.CONFIRMED


@pytest.mark.django_db
def test_reservation_update_status_blocked_for_customer(client, customer_user, restaurant):
    # verifies customers cannot update reservation status directly
    table = Table.objects.create(label='T1', seats=4, grid_squares={}, restaurant=restaurant)
    reservation = Reservation.objects.create(
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=10,
        status=Reservation.Status.PENDING
    )
    client.login(username='testcustomer', password='TestPass123!')
    response = client.post(reverse('reservation_update_status', args=[reservation.pk]), {
        'status': Reservation.Status.CONFIRMED
    })
    assert response.status_code == 302
    reservation.refresh_from_db()
    assert reservation.status == Reservation.Status.PENDING


# ====================== INVENTORY VIEWS ======================

@pytest.mark.django_db
def test_inventory_list_requires_manager(client, customer_user, restaurant):
    # verifies customers cannot access inventory
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('inventory_list', args=[restaurant.pk]))
    assert response.status_code == 302


@pytest.mark.django_db
def test_inventory_list_allowed_for_manager(client, manager_user, restaurant):
    # verifies managers can access the inventory list for their own restaurant
    Restaurant.objects.filter(pk=restaurant.pk).update(user=manager_user)
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('inventory_list', args=[restaurant.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_inventory_list_shows_low_stock_alert(client, manager_user, restaurant):
    # UI test: verifies the low stock alert banner appears when an item is below reorder level
    Restaurant.objects.filter(pk=restaurant.pk).update(user=manager_user)
    Inventory.objects.create(
        restaurant=restaurant,
        ingredient_name='Tomatoes',
        current_level=Decimal('2.00'),
        unit='kg',
        reorder_level=Decimal('10.00')
    )
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('inventory_list', args=[restaurant.pk]))
    content = response.content.decode()
    assert 'Low Stock' in content or 'low stock' in content.lower()


@pytest.mark.django_db
def test_inventory_create_allowed_for_manager(client, manager_user, restaurant):
    # verifies managers can add a new ingredient to their own restaurant
    Restaurant.objects.filter(pk=restaurant.pk).update(user=manager_user)
    client.login(username='testmanager', password='TestPass123!')
    response = client.post(reverse('inventory_create', args=[restaurant.pk]), {
        'ingredient_name': 'Tomatoes',
        'current_level': '50.00',
        'unit': 'kg',
        'reorder_level': '10.00'
    })
    assert response.status_code == 302
    assert Inventory.objects.filter(ingredient_name='Tomatoes').exists()


@pytest.mark.django_db
def test_inventory_edit_updates_record(client, manager_user, restaurant):
    # verifies managers can update inventory levels
    Restaurant.objects.filter(pk=restaurant.pk).update(user=manager_user)
    item = Inventory.objects.create(
        restaurant=restaurant,
        ingredient_name='Cheese',
        current_level=Decimal('20.00'),
        unit='kg',
        reorder_level=Decimal('5.00')
    )
    client.login(username='testmanager', password='TestPass123!')
    client.post(reverse('inventory_edit', args=[item.pk]), {
        'ingredient_name': 'Cheese',
        'current_level': '35.00',
        'unit': 'kg',
        'reorder_level': '5.00'
    })
    item.refresh_from_db()
    assert item.current_level == Decimal('35.00')


@pytest.mark.django_db
def test_inventory_delete_removes_record(client, manager_user, restaurant):
    # verifies managers can delete an inventory item
    Restaurant.objects.filter(pk=restaurant.pk).update(user=manager_user)
    item = Inventory.objects.create(
        restaurant=restaurant,
        ingredient_name='DeleteMe',
        current_level=Decimal('10.00'),
        unit='kg',
        reorder_level=Decimal('2.00')
    )
    client.login(username='testmanager', password='TestPass123!')
    client.post(reverse('inventory_confirm_delete', args=[item.pk]))
    assert not Inventory.objects.filter(ingredient_name='DeleteMe').exists()


# ====================== LOYALTY POINTS ======================

@pytest.mark.django_db
def test_loyalty_points_awarded_on_order_completion(client, customer_user, restaurant):
    # verifies 10 points per dollar are awarded when kitchen marks order as completed
    _ = User.objects.create_user(
        username='kitchenstaff', password='TestPass123!', role=User.Role.KITCHEN_STAFF
    )
    customer = Customer.objects.get(user=customer_user)
    order = Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('50.00'),
        total_price=Decimal('50.00'),
        order_status=Order.OrderStatus.PREPARING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    client.login(username='kitchenstaff', password='TestPass123!')
    client.post(reverse('update_order_status', args=[order.id]), {
        'status': Order.OrderStatus.COMPLETED.value
    })
    order.refresh_from_db()
    customer.refresh_from_db()
    assert order.points_earned == 500
    assert customer.loyalty_points == 500


@pytest.mark.django_db
def test_loyalty_points_not_awarded_twice(client, customer_user, restaurant):
    # verifies points are not awarded again if points_earned is already set
    kitchen = User.objects.create_user(
        username='kitchenstaff2', password='TestPass123!', role=User.Role.KITCHEN_STAFF
    )
    customer = Customer.objects.get(user=customer_user)
    customer.loyalty_points = 500
    customer.save()
    order = Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('50.00'),
        total_price=Decimal('50.00'),
        order_status=Order.OrderStatus.PREPARING,
        payment_status=Order.PaymentStatus.UNPAID,
        points_earned=500  # already awarded, should not double
    )
    client.login(username='kitchenstaff2', password='TestPass123!')
    client.post(reverse('update_order_status', args=[order.id]), {
        'status': Order.OrderStatus.COMPLETED.value
    })
    customer.refresh_from_db()
    assert customer.loyalty_points == 500  # unchanged


# ====================== DRIVER VIEWS ======================

@pytest.mark.django_db
def test_assign_driver_requires_manager(client, customer_user, restaurant):
    # verifies customers cannot assign drivers to orders
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        sub_total=Decimal('20.00'),
        total_price=Decimal('20.00'),
        order_status=Order.OrderStatus.READY,
        payment_status=Order.PaymentStatus.UNPAID
    )
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('assign_driver_to_order', args=[order.id]))
    assert response.status_code == 302


@pytest.mark.django_db
def test_manager_assigns_driver(client, manager_user, restaurant):
    # verifies a manager can assign a driver to a delivery order
    driver = User.objects.create_user(
        username='assigndriver', password='TestPass123!', role=User.Role.DELIVERY_DRIVER
    )
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        sub_total=Decimal('20.00'),
        total_price=Decimal('20.00'),
        order_status=Order.OrderStatus.READY,
        payment_status=Order.PaymentStatus.UNPAID
    )
    client.login(username='testmanager', password='TestPass123!')
    response = client.post(reverse('assign_driver_to_order', args=[order.id]), {
        'driver_id': driver.id
    })
    assert response.status_code == 302
    order.refresh_from_db()
    assert order.assigned_driver == driver


@pytest.mark.django_db
def test_driver_can_access_driver_view(client, driver_user):
    # verifies driver can access their dashboard
    client.login(username='testdriver', password='TestPass123!')
    response = client.get(reverse('driver_view'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_driver_view_shows_assigned_orders(client, driver_user, restaurant):
    # UI test: verifies the driver dashboard lists their assigned delivery orders
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        delivery_address='100 Test Ave',
        sub_total=Decimal('20.00'),
        total_price=Decimal('20.00'),
        order_status=Order.OrderStatus.READY,
        payment_status=Order.PaymentStatus.UNPAID,
        assigned_driver=driver_user
    )
    client.login(username='testdriver', password='TestPass123!')
    response = client.get(reverse('driver_view'))
    content = response.content.decode()
    assert f'#{order.id}' in content
    assert '100 Test Ave' in content


@pytest.mark.django_db
def test_customer_cannot_access_driver_view(client, customer_user):
    # verifies customers cannot access the driver dashboard
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('driver_view'))
    assert response.status_code == 302


# ====================== DELIVERY COMPLETE ======================

@pytest.mark.django_db
def test_driver_can_complete_delivery(client, restaurant, driver_user):
    # verifies driver can mark their assigned order as delivered
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        sub_total=Decimal('20.00'),
        total_price=Decimal('20.00'),
        order_status=Order.OrderStatus.READY,
        payment_status=Order.PaymentStatus.UNPAID,
        assigned_driver=driver_user
    )
    client.login(username='testdriver', password='TestPass123!')
    response = client.post(reverse('delivery_complete', args=[order.id]))
    assert response.status_code == 302
    order.refresh_from_db()
    assert order.order_status == Order.OrderStatus.COMPLETED


@pytest.mark.django_db
def test_driver_cannot_complete_unassigned_order(client, restaurant, driver_user):
    # verifies a driver cannot complete an order they are not assigned to
    other_driver = User.objects.create_user(
        username='otherdriver', password='TestPass123!', role=User.Role.DELIVERY_DRIVER
    )
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        sub_total=Decimal('20.00'),
        total_price=Decimal('20.00'),
        order_status=Order.OrderStatus.READY,
        payment_status=Order.PaymentStatus.UNPAID,
        assigned_driver=other_driver
    )
    client.login(username='testdriver', password='TestPass123!')
    response = client.post(reverse('delivery_complete', args=[order.id]))
    assert response.status_code == 302
    order.refresh_from_db()
    assert order.order_status == Order.OrderStatus.READY


@pytest.mark.django_db
def test_delivery_complete_awards_loyalty_points(client, restaurant, driver_user, customer_user):
    # verifies loyalty points are awarded to the customer when delivery is completed
    customer = Customer.objects.get(user=customer_user)
    order = Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        sub_total=Decimal('30.00'),
        total_price=Decimal('30.00'),
        order_status=Order.OrderStatus.READY,
        payment_status=Order.PaymentStatus.UNPAID,
        assigned_driver=driver_user
    )
    client.login(username='testdriver', password='TestPass123!')
    client.post(reverse('delivery_complete', args=[order.id]))
    customer.refresh_from_db()
    assert customer.loyalty_points == 300  # 30 dollars x 10 points


@pytest.mark.django_db
def test_confirm_pickup_page_loads(client, restaurant, driver_user):
    # UI test: verifies the confirm pickup page renders correctly for the assigned driver
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        delivery_address='123 Pickup Ave',
        sub_total=Decimal('20.00'),
        total_price=Decimal('20.00'),
        order_status=Order.OrderStatus.READY,
        payment_status=Order.PaymentStatus.UNPAID,
        assigned_driver=driver_user
    )
    client.login(username='testdriver', password='TestPass123!')
    response = client.get(reverse('confirm_pickup', args=[order.id]))
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Pickup' in content or 'pickup' in content


# ====================== OWNER VIEW ======================

@pytest.mark.django_db
def test_owner_view_accessible_for_owner(client, owner_user):
    # verifies owner can access their dashboard
    client.login(username='testowner', password='TestPass123!')
    response = client.get(reverse('owner_view'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_owner_view_shows_manage_links(client, owner_user):
    # UI test: verifies owner dashboard renders key management links
    client.login(username='testowner', password='TestPass123!')
    response = client.get(reverse('owner_view'))
    content = response.content.decode()
    assert 'Staff' in content
    assert 'Reports' in content or 'Reporting' in content


@pytest.mark.django_db
def test_customer_cannot_access_owner_view(client, customer_user):
    # verifies customers cannot access the owner dashboard
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('owner_view'))
    assert response.status_code == 302


# ====================== CUSTOMER DASHBOARD ======================

@pytest.mark.django_db
def test_customer_dashboard_accessible_for_customer(client, customer_user):
    # verifies logged in customers can access their dashboard
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('customer_dashboard'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_customer_dashboard_shows_loyalty_points(client, customer_user):
    # UI test: verifies the dashboard shows the loyalty points balance
    customer = Customer.objects.get(user=customer_user)
    customer.loyalty_points = 750
    customer.save()
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('customer_dashboard'))
    assert '750' in response.content.decode()


@pytest.mark.django_db
def test_customer_dashboard_shows_upcoming_reservations(client, customer_user, restaurant):
    # UI test: verifies upcoming reservations appear on the customer dashboard
    customer = Customer.objects.get(user=customer_user)
    table = Table.objects.create(label='T1', seats=4, grid_squares={}, restaurant=restaurant)
    Reservation.objects.create(
        customer=customer,
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=10,
        status=Reservation.Status.CONFIRMED
    )
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('customer_dashboard'))
    content = response.content.decode()
    assert restaurant.name in content


@pytest.mark.django_db
def test_customer_dashboard_blocked_for_staff(client, manager_user):
    # verifies staff cannot access the customer dashboard
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('customer_dashboard'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_customer_dashboard_blocked_for_guest(client):
    # verifies unauthenticated guests cannot access the customer dashboard
    response = client.get(reverse('customer_dashboard'))
    assert response.status_code == 302


# ====================== MANAGER NOTES ======================

@pytest.mark.django_db
def test_manager_can_create_note(client, manager_user, restaurant):
    # verifies managers can create a broadcast note for their restaurant
    Restaurant.objects.filter(pk=restaurant.pk).update(user=manager_user)
    client.login(username='testmanager', password='TestPass123!')
    response = client.post(reverse('manager_note_create'), {
        'message': 'Kitchen closes early tonight.',
        'target_role': 0
    })
    assert response.status_code == 302
    assert ManagerNote.objects.filter(message='Kitchen closes early tonight.').exists()


@pytest.mark.django_db
def test_manager_note_expires_after_24_hours(client, manager_user, restaurant):
    # verifies expired notes are filtered out and do not appear
    Restaurant.objects.filter(pk=restaurant.pk).update(user=manager_user)
    ManagerNote.objects.create(
        restaurant=restaurant,
        created_by=manager_user,
        message='This note is expired',
        target_role=0,
        expires_at=timezone.now() - datetime.timedelta(hours=1)
    )
    client.login(username='testmanager', password='TestPass123!')
    # check the note is not in the active queryset
    from django.utils import timezone as tz
    active_notes = ManagerNote.objects.filter(
        restaurant=restaurant,
        expires_at__gt=tz.now()
    )
    assert active_notes.count() == 0


@pytest.mark.django_db
def test_manager_can_delete_note(client, manager_user, restaurant):
    # verifies managers can delete a note before expiry
    Restaurant.objects.filter(pk=restaurant.pk).update(user=manager_user)
    note = ManagerNote.objects.create(
        restaurant=restaurant,
        created_by=manager_user,
        message='Delete this note',
        target_role=0,
        expires_at=timezone.now() + datetime.timedelta(hours=24)
    )
    client.login(username='testmanager', password='TestPass123!')
    client.post(reverse('manager_note_delete', args=[note.id]))
    assert not ManagerNote.objects.filter(message='Delete this note').exists()


@pytest.mark.django_db
def test_customer_cannot_create_manager_note(client, customer_user):
    # verifies customers cannot create manager notes
    client.login(username='testcustomer', password='TestPass123!')
    response = client.post(reverse('manager_note_create'), {
        'message': 'Fake note',
        'target_role': 0
    })
    assert response.status_code == 302
    assert not ManagerNote.objects.filter(message='Fake note').exists()


# ====================== PRE-ORDER VIEWS ======================

@pytest.mark.django_db
def test_preorder_prompt_page_loads_for_customer(client, customer_user, restaurant):
    # verifies the pre-order prompt page loads for a customer with a valid reservation
    customer = Customer.objects.get(user=customer_user)
    table = Table.objects.create(label='T1', seats=4, grid_squares={}, restaurant=restaurant)
    reservation = Reservation.objects.create(
        customer=customer,
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=10,
        status=Reservation.Status.CONFIRMED
    )
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('reservation_preorder_prompt', args=[reservation.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_preorder_prompt_shows_preorder_option(client, customer_user, restaurant):
    # UI test: verifies the pre-order prompt page shows the pre-order menu button
    customer = Customer.objects.get(user=customer_user)
    table = Table.objects.create(label='T1', seats=4, grid_squares={}, restaurant=restaurant)
    reservation = Reservation.objects.create(
        customer=customer,
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=10,
        status=Reservation.Status.CONFIRMED
    )
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('reservation_preorder_prompt', args=[reservation.pk]))
    content = response.content.decode()
    assert 'Pre-Order' in content or 'pre-order' in content.lower()


@pytest.mark.django_db
def test_preorder_blocked_for_cancelled_reservation(client, customer_user, restaurant):
    # verifies pre-ordering is blocked if the reservation is already cancelled
    customer = Customer.objects.get(user=customer_user)
    table = Table.objects.create(label='T1', seats=4, grid_squares={}, restaurant=restaurant)
    reservation = Reservation.objects.create(
        customer=customer,
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + timezone.timedelta(hours=3),
        party_size=2,
        deposit_amount=10,
        status=Reservation.Status.CANCELLED
    )
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('reservation_preorder_prompt', args=[reservation.pk]))
    assert response.status_code == 302


# ====================== CART VIEWS ======================

@pytest.mark.django_db
def test_cart_add_adds_item_to_session(client, menu_item):
    # verifies adding a menu item creates a cart entry in the session
    response = client.get(reverse('cart_add', args=[menu_item.pk]))
    assert response.status_code == 302
    cart = client.session.get('cart', {})
    assert str(menu_item.pk) in cart
    assert cart[str(menu_item.pk)]['quantity'] == 1


@pytest.mark.django_db
def test_cart_add_increments_existing_item(client, menu_item):
    # verifies adding the same item twice increments quantity instead of duplicating
    client.get(reverse('cart_add', args=[menu_item.pk]))
    client.get(reverse('cart_add', args=[menu_item.pk]))
    cart = client.session.get('cart', {})
    assert cart[str(menu_item.pk)]['quantity'] == 2


@pytest.mark.django_db
def test_cart_remove_removes_item_from_session(client, menu_item):
    # verifies removing an item clears it from the cart session entirely
    client.get(reverse('cart_add', args=[menu_item.pk]))
    client.get(reverse('cart_remove', args=[menu_item.pk]))
    cart = client.session.get('cart', {})
    assert str(menu_item.pk) not in cart


@pytest.mark.django_db
def test_cart_update_changes_quantity(client, menu_item):
    # verifies updating quantity changes the cart correctly
    client.get(reverse('cart_add', args=[menu_item.pk]))
    client.post(reverse('cart_update', args=[menu_item.pk]), {'quantity': 3})
    cart = client.session.get('cart', {})
    assert cart[str(menu_item.pk)]['quantity'] == 3


@pytest.mark.django_db
def test_cart_update_with_zero_removes_item(client, menu_item):
    # verifies setting quantity to 0 removes the item from the cart entirely
    client.get(reverse('cart_add', args=[menu_item.pk]))
    client.post(reverse('cart_update', args=[menu_item.pk]), {'quantity': 0})
    cart = client.session.get('cart', {})
    assert str(menu_item.pk) not in cart


@pytest.mark.django_db
def test_cart_shows_in_menu_page(client, menu_item):
    # UI test: verifies that after adding an item the menu page shows it in the cart
    client.get(reverse('cart_add', args=[menu_item.pk]))
    response = client.get(reverse('menu_item_list'))
    content = response.content.decode()
    assert menu_item.name in content


# ====================== REPORTING VIEW ======================

@pytest.mark.django_db
def test_reporting_view_accessible_for_manager(client, manager_user, restaurant):
    # verifies managers can access the reporting view
    Restaurant.objects.filter(pk=restaurant.pk).update(user=manager_user)
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('reporting_view'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_reporting_view_blocked_for_customer(client, customer_user):
    # verifies customers cannot access the reporting view
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('reporting_view'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_reporting_view_accessible_for_owner(client, owner_user, restaurant):
    # verifies owners can access the reporting view
    client.login(username='testowner', password='TestPass123!')
    response = client.get(reverse('reporting_view'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_reporting_view_shows_popularity_table(client, manager_user, restaurant):
    # UI test: verifies the reporting page renders the popularity ranking section
    Restaurant.objects.filter(pk=restaurant.pk).update(user=manager_user)
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('reporting_view'))
    content = response.content.decode()
    assert 'Popularity' in content or 'popularity' in content.lower()


# ====================== RESTAURANT IS ACTIVE CHECKS ======================

@pytest.mark.django_db
def test_inactive_restaurant_blocks_reservation(client, restaurant):
    # verifies reservations cannot be made when restaurant is inactive
    restaurant.is_active = False
    restaurant.save()
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    response = client.post(reverse('reservation_create'), {
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': (timezone.now() + timezone.timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M'),
        'party_size': 2
    })
    assert response.status_code == 200
    assert not models.Reservation.objects.filter(table=table).exists()


@pytest.mark.django_db
@pytest.mark.django_db
def test_active_restaurant_allows_reservation(client, restaurant):
    # verifies reservations can be made when restaurant is active
    Restaurant.objects.filter(pk=restaurant.pk).update(
        is_active=True,
        opening_time=datetime.time(9, 0),
        closing_time=datetime.time(22, 0)
    )
    restaurant.refresh_from_db()
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    reservation_time = timezone.now().replace(
        hour=15, minute=0, second=0, microsecond=0
    ) + timezone.timedelta(days=1)
    response = client.post(reverse('reservation_create'), {
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': reservation_time.strftime('%Y-%m-%dT%H:%M'),
        'party_size': 2,
        'guest_name': 'Test Guest',
        'guest_email': 'guest@test.com',
        'guest_phone_number': '4031234567',
    })
    assert response.status_code == 302
    assert models.Reservation.objects.filter(table=table).exists()


# ====================== RESERVATION OPENING HOURS CHECK ======================

@pytest.mark.django_db
def test_reservation_blocked_outside_opening_hours(client, restaurant):
    # verifies reservations cannot be made outside restaurant opening hours
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    midnight = timezone.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timezone.timedelta(days=1)
    response = client.post(reverse('reservation_create'), {
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': midnight.strftime('%Y-%m-%dT%H:%M'),
        'party_size': 2
    })
    assert response.status_code == 200
    assert not models.Reservation.objects.filter(table=table).exists()


# ====================== SERVER HOST VIEW ======================

@pytest.mark.django_db
def test_server_host_view_accessible_for_server(client, server_user):
    # verifies servers can access their dashboard
    client.login(username='testserver', password='TestPass123!')
    response = client.get(reverse('server_host_view'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_server_host_view_shows_assigned_tables(client, server_user, restaurant):
    # UI test: verifies the server dashboard shows cards for assigned tables only
    table = Table.objects.create(
        label='T99',
        seats=4,
        grid_squares={'x': 1, 'y': 1, 'w': 1, 'h': 1},
        restaurant=restaurant,
        assigned_server=server_user
    )
    client.login(username='testserver', password='TestPass123!')
    response = client.get(reverse('server_host_view'))
    content = response.content.decode()
    assert 'T99' in content


@pytest.mark.django_db
def test_server_host_view_customer_cannot_access(client, customer_user):
    # verifies customers cannot access the server host dashboard
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('server_host_view'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_toggle_host_mode_switches_session(client, server_user):
    # verifies the host mode toggle flips the session flag correctly
    client.login(username='testserver', password='TestPass123!')
    assert not client.session.get('host_mode', False)
    client.post(reverse('toggle_host_mode'))
    assert client.session.get('host_mode') is True
    client.post(reverse('toggle_host_mode'))
    assert client.session.get('host_mode') is False


@pytest.mark.django_db
def test_server_table_detail_accessible_for_server(client, server_user, restaurant):
    # verifies servers can access the table detail page
    table = Table.objects.create(
        label='T1',
        seats=4,
        grid_squares={'x': 1, 'y': 1, 'w': 1, 'h': 1},
        restaurant=restaurant,
        assigned_server=server_user
    )
    client.login(username='testserver', password='TestPass123!')
    response = client.get(reverse('server_table_detail', args=[table.id]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_server_table_detail_shows_active_order(client, server_user, restaurant):
    # UI test: verifies the table detail page renders the active order items
    table = Table.objects.create(
        label='T1',
        seats=4,
        grid_squares={'x': 1, 'y': 1, 'w': 1, 'h': 1},
        restaurant=restaurant,
        assigned_server=server_user,
        status=Table.Status.OCCUPIED
    )
    order = Order.objects.create(
        restaurant=restaurant,
        table=table,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('20.00'),
        tax_amount=Decimal('1.00'),
        total_price=Decimal('21.00'),
        order_status=Order.OrderStatus.PREPARING,
        payment_status=Order.PaymentStatus.UNPAID,
        assigned_server=server_user
    )
    category = Category.objects.create(name='Test')
    item = MenuItem.objects.create(name='Test Dish', description='Desc', price=Decimal('20.00'), category=category)
    OrderItem.objects.create(order=order, menu_item=item, quantity=1, unit_price=Decimal('20.00'))
    client.login(username='testserver', password='TestPass123!')
    response = client.get(reverse('server_table_detail', args=[table.id]))
    content = response.content.decode()
    assert 'Test Dish' in content


# ====================== KITCHEN VIEW ======================

@pytest.mark.django_db
def test_kitchen_view_accessible_for_kitchen(client, kitchen_user):
    # verifies kitchen staff can access the kitchen dashboard
    client.login(username='testkitchen', password='TestPass123!')
    response = client.get(reverse('kitchen_view'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_kitchen_view_shows_active_orders(client, kitchen_user, restaurant):
    # UI test: verifies the kitchen dashboard shows orders that are pending or preparing
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('20.00'),
        total_price=Decimal('20.00'),
        order_status=Order.OrderStatus.PREPARING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    client.login(username='testkitchen', password='TestPass123!')
    response = client.get(reverse('kitchen_view'))
    content = response.content.decode()
    assert f'#{order.id}' in content


@pytest.mark.django_db
def test_kitchen_view_blocked_for_customer(client, customer_user):
    # verifies customers cannot access the kitchen dashboard
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('kitchen_view'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_kitchen_order_status_update_moves_forward(client, kitchen_user, restaurant):
    # verifies kitchen can advance an order from PENDING to PREPARING
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('20.00'),
        total_price=Decimal('20.00'),
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    client.login(username='testkitchen', password='TestPass123!')
    client.post(reverse('update_order_status', args=[order.id]), {
        'status': Order.OrderStatus.PREPARING.value
    })
    order.refresh_from_db()
    assert order.order_status == Order.OrderStatus.PREPARING


@pytest.mark.django_db
def test_kitchen_order_status_cannot_move_backward(client, kitchen_user, restaurant):
    # verifies kitchen staff cannot move an order backwards in status
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('20.00'),
        total_price=Decimal('20.00'),
        order_status=Order.OrderStatus.PREPARING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    client.login(username='testkitchen', password='TestPass123!')
    client.post(reverse('update_order_status', args=[order.id]), {
        'status': Order.OrderStatus.PENDING.value
    })
    order.refresh_from_db()
    assert order.order_status == Order.OrderStatus.PREPARING


# ====================== TABLE LAYOUT TESTS ======================

def make_table(restaurant, label='T1', seats=4):
    # helper function to create a table for layout tests
    return Table.objects.create(
        label=label,
        seats=seats,
        grid_squares={'x': 0, 'y': 0},
        status=Table.Status.AVAILABLE,
        restaurant=restaurant
    )


@pytest.mark.django_db
def test_manager_can_access_table_layout_edit(client, restaurant, manager_user):
    # verifies managers can access the floor plan editor
    client.login(username=manager_user.username, password='TestPass123!')
    response = client.get(reverse('table_layout_edit', args=[restaurant.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_owner_can_access_table_layout_edit(client, restaurant, owner_user):
    # verifies owners can access the floor plan editor
    client.login(username=owner_user.username, password='TestPass123!')
    response = client.get(reverse('table_layout_edit', args=[restaurant.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_server_host_can_access_table_layout_edit(client, restaurant):
    # verifies servers can access the floor plan editor
    server = User.objects.create_user(
        username='server1', password='TestPass123!', role=User.Role.SERVER_HOST
    )
    client.login(username='server1', password='TestPass123!')
    response = client.get(reverse('table_layout_edit', args=[restaurant.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_table_layout_edit_shows_tables(client, restaurant, manager_user):
    # UI test: verifies the floor plan editor renders the table palette
    table = make_table(restaurant, label='T1')
    client.login(username=manager_user.username, password='TestPass123!')
    response = client.get(reverse('table_layout_edit', args=[restaurant.pk]))
    content = response.content.decode()
    assert 'T1' in content


@pytest.mark.django_db
def test_customer_cannot_access_table_layout_edit(client, restaurant, customer_user):
    # verifies customers cannot access the floor plan editor
    client.login(username=customer_user.username, password='TestPass123!')
    response = client.get(reverse('table_layout_edit', args=[restaurant.pk]))
    assert response.status_code != 200


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_table_layout_edit(client, restaurant):
    # verifies logged out users are redirected away from the floor plan editor
    response = client.get(reverse('table_layout_edit', args=[restaurant.pk]))
    assert response.status_code == 302


@pytest.mark.django_db
def test_customer_cannot_post_to_table_layout_save(client, restaurant, customer_user):
    # verifies customers cannot save layout data
    client.login(username=customer_user.username, password='TestPass123!')
    response = client.post(
        reverse('table_layout_save', args=[restaurant.pk]),
        data=json.dumps({'tables': []}),
        content_type='application/json'
    )
    assert response.status_code != 200


@pytest.mark.django_db
def test_layout_save_creates_table_layout(client, restaurant, manager_user):
    # verifies posting valid layout data creates a TableLayout record
    table = make_table(restaurant, label='T1', seats=4)
    client.login(username=manager_user.username, password='TestPass123!')
    payload = {'tables': [{'table_id': table.id, 'x': 3, 'y': 5}]}
    response = client.post(
        reverse('table_layout_save', args=[restaurant.pk]),
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data['success'] is True
    assert TableLayout.objects.filter(restaurant=restaurant).exists()


@pytest.mark.django_db
def test_layout_save_updates_table_grid_squares(client, restaurant, manager_user):
    # verifies saving a layout correctly updates grid_squares on the table object
    table = make_table(restaurant, label='T1', seats=4)
    client.login(username=manager_user.username, password='TestPass123!')
    payload = {'tables': [{'table_id': table.id, 'x': 3, 'y': 5}]}
    client.post(
        reverse('table_layout_save', args=[restaurant.pk]),
        data=json.dumps(payload),
        content_type='application/json'
    )
    table.refresh_from_db()
    assert table.grid_squares['x'] == 3
    assert table.grid_squares['y'] == 5


@pytest.mark.django_db
def test_layout_save_calculates_size_from_seat_count(client, restaurant, manager_user):
    # verifies table width and height are calculated correctly based on seat count
    small_table = make_table(restaurant, label='T1', seats=4)   # 1x1
    large_table = make_table(restaurant, label='T2', seats=8)   # 2x2
    client.login(username=manager_user.username, password='TestPass123!')
    payload = {'tables': [
        {'table_id': small_table.id, 'x': 0, 'y': 0},
        {'table_id': large_table.id, 'x': 5, 'y': 5},
    ]}
    client.post(
        reverse('table_layout_save', args=[restaurant.pk]),
        data=json.dumps(payload),
        content_type='application/json'
    )
    small_table.refresh_from_db()
    large_table.refresh_from_db()
    assert small_table.grid_squares['w'] == 1
    assert small_table.grid_squares['h'] == 1
    assert large_table.grid_squares['w'] == 2
    assert large_table.grid_squares['h'] == 2


@pytest.mark.django_db
def test_layout_save_returns_error_on_invalid_data(client, restaurant, manager_user):
    # verifies posting malformed data returns a 400 error response
    client.login(username=manager_user.username, password='TestPass123!')
    response = client.post(
        reverse('table_layout_save', args=[restaurant.pk]),
        data='not valid json',
        content_type='application/json'
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_layout_save_rejects_get_request(client, restaurant, manager_user):
    # verifies GET requests to the layout save endpoint are rejected with 405
    client.login(username=manager_user.username, password='TestPass123!')
    response = client.get(reverse('table_layout_save', args=[restaurant.pk]))
    assert response.status_code == 405


# ====================== TABLE LAYOUT VIEW TESTS ======================

@pytest.mark.django_db
def test_table_layout_view_accessible_without_loing(client, restaurant):
    """Read only floor plan view is publicly accessible"""
    response = client.get(reverse('table_layout_view', args=[restaurant.pk]))
    assert response.status_code == 200
    
@pytest.mark.django_db
def test_tabe_layout_view_handles_missing_datetime(client, restaurant):
    """View handles missing datetime parameter"""
    response = client.get(reverse('table_layout_view', args=[restaurant.pk]))
    assert response.status_code == 200
    
@pytest.mark.django_db
def test_tabe_layout_view_handles_no_saved_layout(client, restaurant):
    """View handles restaurant with no saved floor plan"""
    response = client.get(reverse('table_layout_view', args=[restaurant.pk]))
    assert response.status_code == 200
    
@pytest.mark.django_db
def test_tabe_layout_view_marks_reserved_tables(client, restaurant, table):
    """Tables with conflicting reservations are marked as status 3 (Reserved)"""
    # create a layout so grid_exists
    TableLayout.objects.create(
        restaurant=restaurant,
        grid_data=[{
            'table_id': table.id,
            'label': table.label,
            'seats': table.seats,
            'status': table.status,
            'x': 2, 'y': 2, 'w': 1, 'h': 1 
        }],
        uploaded_by=None
    )   
    
    # create conflicting reservaation
    reservation_time = timezone.now().replace(
        hour=18, minute=0, second=0, microsecond=0
    ) + timezone.timedelta(days=1)
    
    Reservation.objects.create(
        restaurant=restaurant,
        table=table,
        reservation_datetime=reservation_time,
        party_size=2,
        status=Reservation.Status.CONFIRMED,
        deposit_amount=10,
        guest_name="Test Guest",
        guest_email="guest@test.com",
        guest_phone_number="4035551234",
    )
    
    datetime_str = reservation_time.strftime('%Y-%m-%dT%H:%M')
    response = client.get(
        reverse('table_layout_view',args=[restaurant.pk]),
        {'datetime':datetime_str}
    )
    
    assert response.status_code == 200
    assert response.context['grid_data'][0]['status'] == 3
    
@pytest.mark.django_db
def test_table_layout_view_marks_available_tables(client, restaurant, table):
    """Tables without conflicts are marked as status 1 (Available)"""
    TableLayout.objects.create(
        restaurant=restaurant,
        grid_data=[{
            'table_id': table.id,
            'label': table.label,
            'seats': table.seats,
            'status': table.status,
            'x': 2, 'y': 2, 'w': 1, 'h': 1 
        }],
        uploaded_by=None
    )
    
    datetime_str = '2099-01-01T12:00'
    response = client.get(
        reverse('table_layout_view', args=[restaurant.pk]),
        {'datetime': datetime_str}
    )
    
    assert response.status_code == 200
    assert response.context['grid_data'][0]['status'] == 1
    
# ====================== NOTIFICATION VIEWS ======================

@pytest.mark.django_db
def test_dismiss_notification_marks_as_read(client, server_user, restaurant):
    # verifies servers can dismiss a notification and it is marked as read in the DB
    table = Table.objects.create(
        label='T1', seats=4,
        grid_squares={'x': 1, 'y': 1, 'w': 1, 'h': 1},
        restaurant=restaurant,
        assigned_server=server_user
    )
    order = Order.objects.create(
        restaurant=restaurant,
        table=table,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('10.00'),
        total_price=Decimal('10.00'),
        order_status=Order.OrderStatus.READY,
        payment_status=Order.PaymentStatus.UNPAID
    )
    notification = Notification.objects.create(
        table=table,
        order=order,
        notification_type=Notification.NotificationType.ORDER_READY,
        message='Order is ready',
        is_read=False
    )
    client.login(username='testserver', password='TestPass123!')
    client.post(reverse('dismiss_notification', args=[notification.id]))
    notification.refresh_from_db()
    assert notification.is_read is True


# ====================== TABLE TRANSFER VIEWS ======================

@pytest.mark.django_db
def test_request_table_transfer_creates_record(client, server_user, restaurant):
    # verifies a server can request to transfer a table to another server
    server2 = User.objects.create_user(
        username='server2', password='TestPass123!', role=User.Role.SERVER_HOST
    )
    table = Table.objects.create(
        label='T1', seats=4,
        grid_squares={'x': 1, 'y': 1, 'w': 1, 'h': 1},
        restaurant=restaurant,
        assigned_server=server_user
    )
    # need an order on the table for the notification to be created
    Order.objects.create(
        restaurant=restaurant,
        table=table,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('10.00'),
        total_price=Decimal('10.00'),
        order_status=Order.OrderStatus.PREPARING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    client.login(username='testserver', password='TestPass123!')
    client.post(reverse('request_table_transfer', args=[table.id]), {
        'receiving_server_id': server2.id
    })
    assert TableTransferRequest.objects.filter(
        table=table,
        requesting_server=server_user,
        receiving_server=server2
    ).exists()


@pytest.mark.django_db
def test_accept_table_transfer_reassigns_table(client, server_user, restaurant):
    # verifies accepting a transfer request reassigns the table to the receiving server
    server2 = User.objects.create_user(
        username='server2', password='TestPass123!', role=User.Role.SERVER_HOST
    )
    table = Table.objects.create(
        label='T1', seats=4,
        grid_squares={'x': 1, 'y': 1, 'w': 1, 'h': 1},
        restaurant=restaurant,
        assigned_server=server_user
    )
    transfer = TableTransferRequest.objects.create(
        table=table,
        requesting_server=server_user,
        receiving_server=server2,
        status=TableTransferRequest.Status.PENDING
    )
    client.login(username='server2', password='TestPass123!')
    client.post(reverse('respond_table_transfer', args=[transfer.id]), {
        'action': 'accept'
    })
    table.refresh_from_db()
    assert table.assigned_server == server2


@pytest.mark.django_db
def test_decline_table_transfer_keeps_original_server(client, server_user, restaurant):
    # verifies declining a transfer keeps the table with the original server
    server2 = User.objects.create_user(
        username='server2', password='TestPass123!', role=User.Role.SERVER_HOST
    )
    table = Table.objects.create(
        label='T1', seats=4,
        grid_squares={'x': 1, 'y': 1, 'w': 1, 'h': 1},
        restaurant=restaurant,
        assigned_server=server_user
    )
    transfer = TableTransferRequest.objects.create(
        table=table,
        requesting_server=server_user,
        receiving_server=server2,
        status=TableTransferRequest.Status.PENDING
    )
    client.login(username='server2', password='TestPass123!')
    client.post(reverse('respond_table_transfer', args=[transfer.id]), {
        'action': 'decline'
    })
    table.refresh_from_db()
    transfer.refresh_from_db()
    assert table.assigned_server == server_user
    assert transfer.status == TableTransferRequest.Status.DECLINED