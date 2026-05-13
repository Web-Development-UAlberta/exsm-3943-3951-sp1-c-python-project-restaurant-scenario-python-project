import pytest
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from restaurant.models import (
    Customer, Restaurant, Category, Tag,
    Table, Order, StaffInvite, MenuItem
)
from restaurant import models
from django.utils import timezone
import datetime

User = get_user_model()


# ====================== HELPER FIXTURES ======================
# Fixtures are reusable setup functions that create test data once and share it across multiple tests
# Instead of repeating the same object creation code in every test, we define it here once
# pytest automatically runs the fixture and passes the created object into any test that lists it as a parameter
# Each fixture runs fresh for every test — no shared state between tests

@pytest.fixture
def restaurant(db):
    # creates a basic restaurant with realistic opening hours for use across tests
    import datetime
    return Restaurant.objects.create(
        name="Test Restaurant",
        address="123 Test St",
        phone_number="403-555-1234",
        opening_time=datetime.time(9, 0),
        closing_time=datetime.time(22, 0),
        latitude=51.044733,
        longitude=-114.0718
    )

@pytest.fixture
def customer_user(db):
    # creates a customer user and their customer profile
    user = User.objects.create_user(
        username='testcustomer',
        password='TestPass123!',
        role=User.Role.CUSTOMER,
        email='customer@test.com'
    )
    Customer.objects.create(
        user=user,
        phone_number='4035551234',
        address='123 Test St'
    )
    return user


@pytest.fixture
def manager_user(db):
    # creates a manager user
    return User.objects.create_user(
        username='testmanager',
        password='TestPass123!',
        role=User.Role.MANAGER
    )


@pytest.fixture
def owner_user(db):
    # creates an owner user
    return User.objects.create_user(
        username='testowner',
        password='TestPass123!',
        role=User.Role.OWNER
    )


# ====================== CUSTOMER AUTH VIEWS ======================

@pytest.mark.django_db
def test_customer_login_page_loads(client):
    # verifies the customer login page returns 200
    response = client.get(reverse('customer_login'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_customer_login_valid_credentials(client, customer_user):
    # verifies a customer can log in with correct credentials
    response = client.post(reverse('customer_login'), {
        'username': 'testcustomer',
        'password': 'TestPass123!'
    })
    assert response.status_code == 302
    assert response.url == reverse('customer_dashboard')


@pytest.mark.django_db
def test_customer_login_invalid_credentials(client, customer_user):
    # verifies login fails with wrong password
    response = client.post(reverse('customer_login'), {
        'username': 'testcustomer',
        'password': 'WrongPassword!'
    })
    assert response.status_code == 200  # stays on login page
    messages = list(response.context['messages'])
    assert any('Invalid' in str(m) for m in messages)


@pytest.mark.django_db
def test_customer_signup_page_loads(client):
    # verifies the signup page returns 200
    response = client.get(reverse('customer_signup'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_customer_signup_creates_account(client):
    # verifies a new customer account is created on valid signup
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
def test_staff_login_blocks_customers(client, customer_user):
    # verifies customers cannot log in via the staff login page
    response = client.post(reverse('staff_login'), {
        'username': 'testcustomer',
        'password': 'TestPass123!'
    })
    assert response.status_code == 200  # stays on staff login page
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
    assert response.status_code == 200  # stays on signup page
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


# ====================== RESTAURANT VIEWS ======================

@pytest.mark.django_db
def test_restaurant_list_page_loads(client):
    # verifies restaurant list page is publicly accessible
    response = client.get(reverse('restaurant_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_restaurant_detail_page_loads(client, restaurant):
    # verifies restaurant detail page loads correctly
    response = client.get(reverse('restaurant_detail', args=[restaurant.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_restaurant_create_requires_owner(client, manager_user):
    # verifies managers cannot create restaurants — only owners can
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('restaurant_create'))
    assert response.status_code == 302  # redirected away


@pytest.mark.django_db
def test_restaurant_create_allowed_for_owner(client, owner_user):
    # verifies owners can access the restaurant create page
    client.login(username='testowner', password='TestPass123!')
    response = client.get(reverse('restaurant_create'))
    assert response.status_code == 200


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


# ====================== TAG VIEWS ======================

@pytest.mark.django_db
def test_tag_list_page_loads(client):
    # verifies tag list is publicly accessible
    response = client.get(reverse('tag_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_tag_create_allowed_for_manager(client, manager_user):
    # verifies managers can create tags
    client.login(username='testmanager', password='TestPass123!')
    response = client.post(reverse('tag_create'), {'name': 'Vegan'})
    assert response.status_code == 302
    assert Tag.objects.filter(name='Vegan').exists()


# ====================== ORDER VIEWS ======================

@pytest.mark.django_db
def test_order_create_redirects_to_menu_when_cart_empty(client):
    # verifies guests with empty cart are redirected to menu to add items first
    # this is the correct behavior — cart must have items before checkout
    response = client.get(reverse('order_create'))
    assert response.status_code == 302
    assert response.url == reverse('menu_item_list')


@pytest.mark.django_db
def test_order_create_redirects_to_menu_when_cart_empty_for_customer(client, customer_user):
    # verifies logged in customers with empty cart are redirected to menu to add items first
    # this is the correct behavior — cart must have items before checkout
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('order_create'))
    assert response.status_code == 302
    assert response.url == reverse('menu_item_list')


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
def test_order_edit_blocked_when_not_pending(client, customer_user, restaurant):
    # verifies customers cannot edit orders that are no longer pending
    customer = Customer.objects.get(user=customer_user)
    order = Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=Order.OrderType.TAKE_OUT,
        sub_total=20.00,
        total_price=20.00,
        order_status=Order.OrderStatus.PREPARING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('order_edit', args=[order.pk]))
    assert response.status_code == 302  # redirected away


# ====================== STAFF INVITE VIEWS ======================

@pytest.mark.django_db
def test_staff_invite_list_requires_manager(client, customer_user):
    # verifies customers cannot access staff invite list
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('staff_invite_list'))
    assert response.status_code == 302


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
    assert response.status_code == 200  # stays on form page
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

    # create first reservation
    models.Reservation.objects.create(
        table=table,
        restaurant=restaurant,
        reservation_datetime=reservation_time,
        party_size=2,
        deposit_amount=10,
        status=models.Reservation.Status.CONFIRMED
    )

    # attempt to book the same table at the same time
    response = client.post(reverse('reservation_create'), {
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': reservation_time.strftime('%Y-%m-%dT%H:%M'),
        'party_size': 2
    })
    assert response.status_code == 200  # stays on form, conflict detected
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
    # verifies no cancellation fee when cancelled 3+ hours before reservation
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
    # restaurant must be linked to the manager user for the scoping check to pass
    Restaurant.objects.filter(pk=restaurant.pk).update(user=manager_user)
    client.login(username='testmanager', password='TestPass123!')
    response = client.get(reverse('inventory_list', args=[restaurant.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_inventory_create_allowed_for_manager(client, manager_user, restaurant):
    # verifies managers can add a new ingredient to their own restaurant
    # restaurant must be linked to the manager user for the scoping check to pass
    Restaurant.objects.filter(pk=restaurant.pk).update(user=manager_user)
    client.login(username='testmanager', password='TestPass123!')
    response = client.post(reverse('inventory_create', args=[restaurant.pk]), {
        'ingredient_name': 'Tomatoes',
        'current_level': '50.00',
        'unit': 'kg',
        'reorder_level': '10.00'
    })
    assert response.status_code == 302
    assert models.Inventory.objects.filter(ingredient_name='Tomatoes').exists()


# ====================== LOYALTY POINTS EARNING ======================

@pytest.mark.django_db
def test_loyalty_points_awarded_on_order_completion(client, customer_user, restaurant):
    # verifies 10 points per dollar are awarded when kitchen marks order as completed
    # we need to create the object for the test, however will not be referencing to it directly
    _ = User.objects.create_user(
        username='kitchenstaff', password='TestPass123!', role=User.Role.KITCHEN_STAFF
    )
    customer = Customer.objects.get(user=customer_user)
    order = models.Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        order_type=models.Order.OrderType.DINE_IN,
        sub_total=50.00,
        total_price=50.00,
        order_status=models.Order.OrderStatus.PREPARING,
        payment_status=models.Order.PaymentStatus.UNPAID
    )
    client.login(username='kitchenstaff', password='TestPass123!')
    client.post(reverse('update_order_status', args=[order.id]), {
        'status': models.Order.OrderStatus.COMPLETED.value
    })
    order.refresh_from_db()
    customer.refresh_from_db()
    assert order.points_earned == 500  # 50 dollars x 10 points
    assert customer.loyalty_points == 500
    
    
# ====================== DRIVER VIEWS ======================

@pytest.mark.django_db
def test_assign_driver_requires_manager(client, customer_user, restaurant):
    """Customers cannot assign drivers to orders"""
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        sub_total=20.00,
        total_price=20.00,
        order_status=Order.OrderStatus.READY,
        payment_status=Order.PaymentStatus.UNPAID
    )
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('assign_driver_to_order', args=[order.id]))
    assert response.status_code == 302
    
@pytest.mark.django_db
def test_manager_assigns_driver(client, manager_user, restaurant):
    """Manager can assign drivers to orders"""
    driver = User.objects.create_user(
        username='testdriver',
        password='TestPass123!',
        role=User.Role.DELIVERY_DRIVER
    )
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        sub_total=20.00,
        total_price=20.00,
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
def test_driver_can_access_driver_view(client):
    """Driver can access their dashbaord"""
    _ = User.objects.create_user(
        username='testdriver',
        password='TestPass123!',
        role=User.Role.DELIVERY_DRIVER
    )
    client.login(username='testdriver', password='TestPass123!')
    response = client.get(reverse('driver_view'))
    assert response.status_code == 200
    
@pytest.mark.django_db
def test_customer_cannot_access_driver_view(client, customer_user):
    """Customer cannot access driver dashbaord"""
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('driver_view'))
    assert response.status_code == 302


# ====================== DELIVERY COMPLETE ======================

@pytest.mark.django_db
def test_driver_can_complete_delivery(client, restaurant):
    # verifies driver can mark their assigned order as delivered
    driver = User.objects.create_user(
        username='testdriver', password='TestPass123!', role=User.Role.DELIVERY_DRIVER
    )
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        sub_total=20.00,
        total_price=20.00,
        order_status=Order.OrderStatus.READY,
        payment_status=Order.PaymentStatus.UNPAID,
        assigned_driver=driver
    )
    client.login(username='testdriver', password='TestPass123!')
    response = client.post(reverse('delivery_complete', args=[order.id]))
    assert response.status_code == 302
    order.refresh_from_db()
    assert order.order_status == Order.OrderStatus.COMPLETED


@pytest.mark.django_db
def test_driver_cannot_complete_unassigned_order(client, restaurant):
    # verifies a driver cannot complete an order they are not assigned to
    _ = User.objects.create_user(
        username='testdriver', password='TestPass123!', role=User.Role.DELIVERY_DRIVER
    )
    other_driver = User.objects.create_user(
        username='otherdriver', password='TestPass123!', role=User.Role.DELIVERY_DRIVER
    )
    order = Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        sub_total=20.00,
        total_price=20.00,
        order_status=Order.OrderStatus.READY,
        payment_status=Order.PaymentStatus.UNPAID,
        assigned_driver=other_driver
    )
    client.login(username='testdriver', password='TestPass123!')
    response = client.post(reverse('delivery_complete', args=[order.id]))
    assert response.status_code == 302
    order.refresh_from_db()
    assert order.order_status == Order.OrderStatus.READY  # unchanged


# ====================== STAFF INVITE DELETE ======================

@pytest.mark.django_db
def test_staff_invite_delete_allowed_for_manager(client, manager_user):
    # verifies managers can revoke an unused invite
    invite = StaffInvite.objects.create(email='revoke@test.com', role=User.Role.SERVER_HOST)
    client.login(username='testmanager', password='TestPass123!')
    response = client.post(reverse('staff_invite_delete', args=[invite.pk]))
    assert response.status_code == 302
    assert not StaffInvite.objects.filter(email='revoke@test.com').exists()


# ====================== OWNER VIEW ======================

@pytest.mark.django_db
def test_owner_view_accessible_for_owner(client, owner_user):
    # verifies owner can access their dashboard
    client.login(username='testowner', password='TestPass123!')
    response = client.get(reverse('owner_view'))
    assert response.status_code == 200


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


@pytest.mark.django_db
def test_customer_dashboard_shows_loyalty_points(client, customer_user):
    # verifies the dashboard context includes the customer object with loyalty points
    client.login(username='testcustomer', password='TestPass123!')
    response = client.get(reverse('customer_dashboard'))
    assert response.status_code == 200
    assert 'customer' in response.context
    assert response.context['customer'].loyalty_points == 0


# ====================== CART VIEWS ======================

@pytest.mark.django_db
def test_cart_add_adds_item_to_session(client, restaurant):
    # verifies adding a menu item creates a cart entry in the session
    category = Category.objects.create(name='Test')
    item = MenuItem.objects.create(
        name='Test Burger', description='Test', price='12.99', category=category
    )
    response = client.get(reverse('cart_add', args=[item.pk]))
    assert response.status_code == 302
    # check the cart was created in the session
    cart = client.session.get('cart', {})
    assert str(item.pk) in cart
    assert cart[str(item.pk)]['quantity'] == 1


@pytest.mark.django_db
def test_cart_add_increments_existing_item(client, restaurant):
    # verifies adding the same item twice increments quantity instead of duplicating
    category = Category.objects.create(name='Test')
    item = MenuItem.objects.create(
        name='Test Burger', description='Test', price='12.99', category=category
    )
    # add the same item twice
    client.get(reverse('cart_add', args=[item.pk]))
    client.get(reverse('cart_add', args=[item.pk]))
    cart = client.session.get('cart', {})
    assert cart[str(item.pk)]['quantity'] == 2


@pytest.mark.django_db
def test_cart_remove_removes_item_from_session(client, restaurant):
    # verifies removing an item clears it from the cart session
    category = Category.objects.create(name='Test')
    item = MenuItem.objects.create(
        name='Test Burger', description='Test', price='12.99', category=category
    )
    # add item first then remove it
    client.get(reverse('cart_add', args=[item.pk]))
    client.get(reverse('cart_remove', args=[item.pk]))
    cart = client.session.get('cart', {})
    assert str(item.pk) not in cart


@pytest.mark.django_db
def test_cart_update_changes_quantity(client, restaurant):
    # verifies updating quantity changes the cart correctly
    category = Category.objects.create(name='Test')
    item = MenuItem.objects.create(
        name='Test Burger', description='Test', price='12.99', category=category
    )
    client.get(reverse('cart_add', args=[item.pk]))
    client.post(reverse('cart_update', args=[item.pk]), {'quantity': 3})
    cart = client.session.get('cart', {})
    assert cart[str(item.pk)]['quantity'] == 3


@pytest.mark.django_db
def test_cart_update_with_zero_removes_item(client, restaurant):
    # verifies setting quantity to 0 removes the item from the cart entirely
    category = Category.objects.create(name='Test')
    item = MenuItem.objects.create(
        name='Test Burger', description='Test', price='12.99', category=category
    )
    client.get(reverse('cart_add', args=[item.pk]))
    client.post(reverse('cart_update', args=[item.pk]), {'quantity': 0})
    cart = client.session.get('cart', {})
    assert str(item.pk) not in cart


# ====================== REPORTING VIEW ======================

@pytest.mark.django_db
def test_reporting_view_accessible_for_manager(client, manager_user, restaurant):
    # verifies managers can access the reporting view
    # restaurant must be linked to the manager user for the view to find it
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


# ====================== RESTAURANT IS_ACTIVE CHECKS ======================

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
    # form should fail validation and stay on the page
    assert response.status_code == 200
    assert not models.Reservation.objects.filter(table=table).exists()


@pytest.mark.django_db
def test_active_restaurant_allows_reservation(client, restaurant):
    # verifies reservations can be made when restaurant is active
    # update opening and closing times to allow the test reservation time
    Restaurant.objects.filter(pk=restaurant.pk).update(
        is_active=True,
        opening_time=datetime.time(9, 0),
        closing_time=datetime.time(22, 0)
    )
    restaurant.refresh_from_db()
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    # using noon UTC which is safely within 09:00 to 22:00 for any North American timezone
    reservation_time = timezone.now().replace(hour=15, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)
    response = client.post(reverse('reservation_create'), {
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': reservation_time.strftime('%Y-%m-%dT%H:%M'),
        'party_size': 2
    })
    assert response.status_code == 302
    assert models.Reservation.objects.filter(table=table).exists()


# ====================== RESERVATION OPENING HOURS CHECK ======================

@pytest.mark.django_db
def test_reservation_blocked_outside_opening_hours(client, restaurant):
    # verifies reservations cannot be made outside restaurant opening hours
    # seed restaurant is open 09:00 to 22:00, so midnight is outside hours
    table = Table.objects.create(
        label='T1', seats=4, grid_squares={}, restaurant=restaurant
    )
    # create a datetime that is definitely outside opening hours (midnight)
    midnight = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)
    response = client.post(reverse('reservation_create'), {
        'restaurant': restaurant.pk,
        'table': table.pk,
        'reservation_datetime': midnight.strftime('%Y-%m-%dT%H:%M'),
        'party_size': 2
    })
    assert response.status_code == 200
    assert not models.Reservation.objects.filter(table=table).exists()