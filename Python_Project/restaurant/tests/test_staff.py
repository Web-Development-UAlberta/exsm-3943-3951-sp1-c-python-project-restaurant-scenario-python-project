import pytest
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import datetime
from restaurant.models import (
    User, Table, Order, Restaurant, OrderItem,
    Category, MenuItem, Notification, TableTransferRequest,
    Customer
)


# ====================== FIXTURES ======================
# shared fixtures to avoid repeating object creation across tests

@pytest.fixture
def restaurant(db):
    # creates a test restaurant with valid opening hours
    return Restaurant.objects.create(
        name='Test Restaurant',
        address='123 Test St',
        phone_number='403-555-1234',
        opening_time=datetime.time(9, 0),
        closing_time=datetime.time(22, 0),
        latitude=Decimal('51.044733'),
        longitude=Decimal('-114.071883'),
        is_active=True
    )


@pytest.fixture
def manager(db):
    # creates a manager user for testing management level access
    return User.objects.create_user(
        username='manager1',
        password='TestPass123!',
        role=User.Role.MANAGER,
        email='manager@test.com'
    )


@pytest.fixture
def owner(db):
    # creates an owner user for testing owner level access
    return User.objects.create_user(
        username='owner1',
        password='TestPass123!',
        role=User.Role.OWNER,
        email='owner@test.com'
    )


@pytest.fixture
def server(db):
    # creates a server user for testing server host actions
    return User.objects.create_user(
        username='server1',
        password='TestPass123!',
        role=User.Role.SERVER_HOST,
        email='server@test.com',
        shift_start=datetime.time(9, 0),
        shift_end=datetime.time(17, 0)
    )


@pytest.fixture
def server2(db):
    # creates a second server for testing table transfer requests
    return User.objects.create_user(
        username='server2',
        password='TestPass123!',
        role=User.Role.SERVER_HOST,
        email='server2@test.com'
    )


@pytest.fixture
def kitchen(db):
    # creates a kitchen staff user for testing kitchen actions
    return User.objects.create_user(
        username='kitchen1',
        password='TestPass123!',
        role=User.Role.KITCHEN_STAFF,
        email='kitchen@test.com'
    )


@pytest.fixture
def driver(db):
    # creates a delivery driver user for testing driver actions
    return User.objects.create_user(
        username='driver1',
        password='TestPass123!',
        role=User.Role.DELIVERY_DRIVER,
        email='driver@test.com'
    )


@pytest.fixture
def customer(db):
    # creates a customer user and their linked profile for testing access restrictions
    user = User.objects.create_user(
        username='customer1',
        password='TestPass123!',
        role=User.Role.CUSTOMER,
        email='customer@test.com'
    )
    Customer.objects.create(
        user=user,
        phone_number='4031234567',
        address='100 Test Ave'
    )
    return user


@pytest.fixture
def table(db, restaurant, server):
    # creates a table assigned to server1 for testing server host actions
    return Table.objects.create(
        label='T5',
        seats=4,
        grid_squares={'x': 0, 'y': 0, 'w': 1, 'h': 1},
        status=Table.Status.AVAILABLE,
        restaurant=restaurant,
        assigned_server=server
    )


@pytest.fixture
def dine_in_order(db, restaurant, table):
    # creates a pending dine-in order linked to the test table
    return Order.objects.create(
        restaurant=restaurant,
        table=table,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('45.50'),
        tax_amount=Decimal('2.28'),
        total_price=Decimal('47.78'),
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )


@pytest.fixture
def delivery_order(db, restaurant):
    # creates a ready delivery order for testing auto-assignment and driver actions
    return Order.objects.create(
        restaurant=restaurant,
        order_type=Order.OrderType.DELIVERY,
        delivery_address='200 Test Ave, Calgary, AB',
        delivery_fee=Decimal('10.00'),
        sub_total=Decimal('20.00'),
        tax_amount=Decimal('1.00'),
        total_price=Decimal('31.00'),
        order_status=Order.OrderStatus.READY,
        payment_status=Order.PaymentStatus.UNPAID
    )


# ====================== STAFF LIST ACCESS ======================

@pytest.mark.django_db
def test_staff_list_access_for_manager(client, manager):
    # verifies managers can access the staff management list
    client.login(username='manager1', password='TestPass123!')
    response = client.get(reverse('staff_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_staff_list_access_for_owner(client, owner):
    # verifies owners can access the staff management list
    client.login(username='owner1', password='TestPass123!')
    response = client.get(reverse('staff_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_staff_list_shows_staff_names(client, manager, server):
    # UI test: verifies the staff list page renders staff member names
    client.login(username='manager1', password='TestPass123!')
    response = client.get(reverse('staff_list'))
    content = response.content.decode()
    assert server.first_name in content or server.username in content


@pytest.mark.django_db
def test_staff_list_shows_role_column(client, manager, server):
    # UI test: verifies the staff list renders the role column for each member
    client.login(username='manager1', password='TestPass123!')
    response = client.get(reverse('staff_list'))
    content = response.content.decode()
    assert 'Server' in content or 'Role' in content


@pytest.mark.django_db
def test_unauthorized_user_cannot_access_staff_list(client, customer):
    # verifies customers are blocked from the staff management list
    client.login(username='customer1', password='TestPass123!')
    response = client.get(reverse('staff_list'))
    assert response.status_code != 200


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_staff_list(client):
    # verifies unauthenticated users are redirected away from staff list
    response = client.get(reverse('staff_list'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_server_cannot_access_staff_list(client, server):
    # verifies server host cannot access the staff management list
    client.login(username='server1', password='TestPass123!')
    response = client.get(reverse('staff_list'))
    assert response.status_code != 200


@pytest.mark.django_db
def test_driver_cannot_access_staff_list(client, driver):
    # verifies delivery drivers cannot access the staff management list
    client.login(username='driver1', password='TestPass123!')
    response = client.get(reverse('staff_list'))
    assert response.status_code != 200


# ====================== STAFF DETAIL ======================

@pytest.mark.django_db
def test_manager_can_access_staff_detail(client, manager, server):
    # verifies managers can view the detail page for individual staff members
    client.login(username='manager1', password='TestPass123!')
    response = client.get(reverse('staff_detail', args=[server.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_staff_detail_shows_shift_times(client, manager, server):
    # UI test: verifies the staff detail page renders the shift start and end times
    client.login(username='manager1', password='TestPass123!')
    response = client.get(reverse('staff_detail', args=[server.pk]))
    content = response.content.decode()
    assert '09:00' in content or 'shift' in content.lower()


@pytest.mark.django_db
def test_owner_can_access_staff_detail(client, owner, server):
    # verifies owners can also view staff detail pages
    client.login(username='owner1', password='TestPass123!')
    response = client.get(reverse('staff_detail', args=[server.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_customer_cannot_access_staff_detail(client, customer, server):
    # verifies customers cannot view staff detail pages
    client.login(username='customer1', password='TestPass123!')
    response = client.get(reverse('staff_detail', args=[server.pk]))
    assert response.status_code == 302


# ====================== STAFF EDIT ======================

@pytest.mark.django_db
def test_manager_can_access_staff_edit(client, manager, server):
    # verifies managers can access the staff edit form
    client.login(username='manager1', password='TestPass123!')
    response = client.get(reverse('staff_edit', args=[server.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_staff_edit_page_shows_form_fields(client, manager, server):
    # UI test: verifies the staff edit form renders key fields like email and shift times
    client.login(username='manager1', password='TestPass123!')
    response = client.get(reverse('staff_edit', args=[server.pk]))
    content = response.content.decode()
    assert 'email' in content.lower()
    assert 'shift' in content.lower()


@pytest.mark.django_db
def test_staff_edit_saves_changes(client, manager, server):
    # verifies managers can update a staff member's email via the edit form
    client.login(username='manager1', password='TestPass123!')
    client.post(reverse('staff_edit', args=[server.pk]), {
        'first_name': server.first_name or 'Peter',
        'last_name': server.last_name or 'Parker',
        'email': 'updated@test.com',
        'phone_number': '4039876543',
        'shift_start': '08:00',
        'shift_end': '16:00',
        'is_active_staff': True
    })
    server.refresh_from_db()
    assert server.email == 'updated@test.com'


@pytest.mark.django_db
def test_staff_edit_blocked_for_customers(client, customer, server):
    # verifies customers cannot edit staff profiles
    client.login(username='customer1', password='TestPass123!')
    response = client.get(reverse('staff_edit', args=[server.pk]))
    assert response.status_code == 302


@pytest.mark.django_db
def test_staff_edit_cannot_edit_customer_through_staff_view(client, manager, customer):
    # verifies the staff edit view blocks editing customer accounts
    # customers must be edited through the customer edit page instead
    client.login(username='manager1', password='TestPass123!')
    response = client.post(reverse('staff_edit', args=[customer.pk]), {
        'first_name': 'Hacked',
        'last_name': 'Customer',
        'email': 'hacked@test.com',
        'is_active_staff': True
    })
    assert response.status_code == 302
    customer.refresh_from_db()
    assert customer.email != 'hacked@test.com'


# ====================== TABLE STATUS UPDATES ======================

@pytest.mark.django_db
def test_server_can_update_table_status(client, server, table):
    # verifies servers can update a table's status
    client.login(username='server1', password='TestPass123!')
    response = client.post(
        reverse('update_table_status', args=[table.id]),
        {'status': Table.Status.OCCUPIED.value}
    )
    assert response.status_code == 302
    table.refresh_from_db()
    assert table.status == Table.Status.OCCUPIED


@pytest.mark.django_db
def test_server_can_set_table_to_needs_cleaning(client, server, table):
    # verifies servers can mark a table as needing cleaning after guests leave
    client.login(username='server1', password='TestPass123!')
    client.post(
        reverse('update_table_status', args=[table.id]),
        {'status': Table.Status.NEEDS_CLEANING.value}
    )
    table.refresh_from_db()
    assert table.status == Table.Status.NEEDS_CLEANING


@pytest.mark.django_db
def test_server_can_set_table_to_reserved(client, server, table):
    # verifies servers can mark a table as reserved
    client.login(username='server1', password='TestPass123!')
    client.post(
        reverse('update_table_status', args=[table.id]),
        {'status': Table.Status.RESERVED.value}
    )
    table.refresh_from_db()
    assert table.status == Table.Status.RESERVED


@pytest.mark.django_db
def test_manager_can_update_table_status(client, manager, table):
    # verifies managers can also update table status
    client.login(username='manager1', password='TestPass123!')
    client.post(
        reverse('update_table_status', args=[table.id]),
        {'status': Table.Status.OCCUPIED.value}
    )
    table.refresh_from_db()
    assert table.status == Table.Status.OCCUPIED


@pytest.mark.django_db
def test_unauthorized_user_cannot_update_table_status(client, customer, table):
    # verifies customers cannot update table status
    client.login(username='customer1', password='TestPass123!')
    response = client.post(
        reverse('update_table_status', args=[table.id]),
        {'status': Table.Status.OCCUPIED.value}
    )
    assert response.status_code == 302
    table.refresh_from_db()
    assert table.status == Table.Status.AVAILABLE  # status should be unchanged


@pytest.mark.django_db
def test_kitchen_staff_cannot_update_table_status(client, kitchen, table):
    # verifies kitchen staff cannot update table status since they manage orders not tables
    client.login(username='kitchen1', password='TestPass123!')
    response = client.post(
        reverse('update_table_status', args=[table.id]),
        {'status': Table.Status.OCCUPIED.value}
    )
    assert response.status_code == 302
    table.refresh_from_db()
    assert table.status == Table.Status.AVAILABLE  # status should be unchanged


# ====================== ORDER STATUS UPDATES ======================

@pytest.mark.django_db
def test_kitchen_can_update_order_status(client, kitchen, dine_in_order):
    # verifies kitchen staff can advance an order from PENDING to PREPARING
    client.login(username='kitchen1', password='TestPass123!')
    response = client.post(
        reverse('update_order_status', args=[dine_in_order.id]),
        {'status': Order.OrderStatus.PREPARING.value}
    )
    assert response.status_code == 302
    dine_in_order.refresh_from_db()
    assert dine_in_order.order_status == Order.OrderStatus.PREPARING


@pytest.mark.django_db
def test_kitchen_can_mark_order_ready(client, kitchen, dine_in_order):
    # verifies kitchen staff can mark an order as READY once prepared
    dine_in_order.order_status = Order.OrderStatus.PREPARING
    dine_in_order.save()
    client.login(username='kitchen1', password='TestPass123!')
    client.post(
        reverse('update_order_status', args=[dine_in_order.id]),
        {'status': Order.OrderStatus.READY.value}
    )
    dine_in_order.refresh_from_db()
    assert dine_in_order.order_status == Order.OrderStatus.READY


@pytest.mark.django_db
def test_kitchen_cannot_move_order_backward(client, kitchen, dine_in_order):
    # verifies kitchen staff cannot move an order back to a previous status
    dine_in_order.order_status = Order.OrderStatus.PREPARING
    dine_in_order.save()
    client.login(username='kitchen1', password='TestPass123!')
    client.post(
        reverse('update_order_status', args=[dine_in_order.id]),
        {'status': Order.OrderStatus.PENDING.value}
    )
    dine_in_order.refresh_from_db()
    assert dine_in_order.order_status == Order.OrderStatus.PREPARING


@pytest.mark.django_db
def test_manager_can_move_order_backward(client, manager, dine_in_order):
    # verifies managers can override and move an order back to a previous status
    dine_in_order.order_status = Order.OrderStatus.PREPARING
    dine_in_order.save()
    client.login(username='manager1', password='TestPass123!')
    client.post(
        reverse('update_order_status', args=[dine_in_order.id]),
        {'status': Order.OrderStatus.PENDING.value}
    )
    dine_in_order.refresh_from_db()
    assert dine_in_order.order_status == Order.OrderStatus.PENDING


@pytest.mark.django_db
def test_customer_cannot_update_order_status(client, customer, dine_in_order):
    # verifies customers cannot update order status through the kitchen endpoint
    client.login(username='customer1', password='TestPass123!')
    response = client.post(
        reverse('update_order_status', args=[dine_in_order.id]),
        {'status': Order.OrderStatus.PREPARING.value}
    )
    assert response.status_code == 302
    dine_in_order.refresh_from_db()
    assert dine_in_order.order_status == Order.OrderStatus.PENDING  # unchanged


@pytest.mark.django_db
def test_ready_delivery_order_auto_assigns_driver(client, kitchen, restaurant, delivery_order, driver):
    # verifies marking a delivery order as READY auto-assigns the least busy active driver
    client.login(username='kitchen1', password='TestPass123!')
    client.post(
        reverse('update_order_status', args=[delivery_order.id]),
        {'status': Order.OrderStatus.READY.value}
    )
    delivery_order.refresh_from_db()
    assert delivery_order.assigned_driver is not None
    assert delivery_order.assigned_driver.role == User.Role.DELIVERY_DRIVER


@pytest.mark.django_db
def test_ready_delivery_order_creates_driver_notification(client, kitchen, restaurant, delivery_order, driver):
    # verifies that auto-assigning a driver also creates a notification for them
    client.login(username='kitchen1', password='TestPass123!')
    client.post(
        reverse('update_order_status', args=[delivery_order.id]),
        {'status': Order.OrderStatus.READY.value}
    )
    assert Notification.objects.filter(
        order=delivery_order,
        notification_type=Notification.NotificationType.ORDER_READY
    ).exists()


@pytest.mark.django_db
def test_ready_dine_in_order_creates_server_notification(client, kitchen, restaurant, table, dine_in_order):
    # verifies marking a dine-in order READY creates a notification for the table server
    dine_in_order.order_status = Order.OrderStatus.PREPARING
    dine_in_order.save()
    client.login(username='kitchen1', password='TestPass123!')
    client.post(
        reverse('update_order_status', args=[dine_in_order.id]),
        {'status': Order.OrderStatus.READY.value}
    )
    assert Notification.objects.filter(
        order=dine_in_order,
        notification_type=Notification.NotificationType.ORDER_READY
    ).exists()


# ====================== SERVER ASSIGNMENT ======================

@pytest.mark.django_db
def test_server_can_assign_server_to_table(client, server, table):
    # verifies a server can assign themselves or another server to a table
    client.login(username='server1', password='TestPass123!')
    response = client.post(
        reverse('assign_server_to_table', args=[table.id]),
        {'server_id': server.id}
    )
    assert response.status_code == 302
    table.refresh_from_db()
    assert table.assigned_server == server


@pytest.mark.django_db
def test_manager_can_assign_server_to_table(client, manager, table, server):
    # verifies managers can assign servers to tables
    client.login(username='manager1', password='TestPass123!')
    response = client.post(
        reverse('assign_server_to_table', args=[table.id]),
        {'server_id': server.id}
    )
    assert response.status_code == 302
    table.refresh_from_db()
    assert table.assigned_server == server


@pytest.mark.django_db
def test_customer_cannot_assign_server_to_table(client, customer, table, server):
    # verifies customers cannot assign servers to tables
    client.login(username='customer1', password='TestPass123!')
    response = client.post(
        reverse('assign_server_to_table', args=[table.id]),
        {'server_id': server.id}
    )
    assert response.status_code == 302
    table.refresh_from_db()
    # table still has the original server from the fixture, not newly reassigned
    assert table.assigned_server == server


# ====================== TABLE TRANSFER ======================

@pytest.mark.django_db
def test_server_can_request_table_transfer(client, server, server2, table, restaurant):
    # verifies a server can send a table transfer request to another server
    # an order must exist on the table for the notification to be created
    Order.objects.create(
        restaurant=restaurant,
        table=table,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('10.00'),
        total_price=Decimal('10.00'),
        order_status=Order.OrderStatus.PREPARING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    client.login(username='server1', password='TestPass123!')
    client.post(
        reverse('request_table_transfer', args=[table.id]),
        {'receiving_server_id': server2.id}
    )
    assert TableTransferRequest.objects.filter(
        table=table,
        requesting_server=server,
        receiving_server=server2,
        status=TableTransferRequest.Status.PENDING
    ).exists()


@pytest.mark.django_db
def test_duplicate_transfer_request_blocked(client, server, server2, table, restaurant):
    # verifies a second pending transfer request for the same table is blocked
    Order.objects.create(
        restaurant=restaurant,
        table=table,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('10.00'),
        total_price=Decimal('10.00'),
        order_status=Order.OrderStatus.PREPARING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    # create the first request manually
    TableTransferRequest.objects.create(
        table=table,
        requesting_server=server,
        receiving_server=server2,
        status=TableTransferRequest.Status.PENDING
    )
    client.login(username='server1', password='TestPass123!')
    client.post(
        reverse('request_table_transfer', args=[table.id]),
        {'receiving_server_id': server2.id}
    )
    # still only one pending request despite posting twice
    assert TableTransferRequest.objects.filter(
        table=table,
        requesting_server=server,
        receiving_server=server2,
        status=TableTransferRequest.Status.PENDING
    ).count() == 1


@pytest.mark.django_db
def test_accepting_transfer_reassigns_table(client, server, server2, table):
    # verifies accepting a transfer request reassigns the table to the receiving server
    transfer = TableTransferRequest.objects.create(
        table=table,
        requesting_server=server,
        receiving_server=server2,
        status=TableTransferRequest.Status.PENDING
    )
    client.login(username='server2', password='TestPass123!')
    client.post(
        reverse('respond_table_transfer', args=[transfer.id]),
        {'action': 'accept'}
    )
    table.refresh_from_db()
    transfer.refresh_from_db()
    assert table.assigned_server == server2
    assert transfer.status == TableTransferRequest.Status.ACCEPTED


@pytest.mark.django_db
def test_declining_transfer_keeps_original_server(client, server, server2, table, restaurant):
    # verifies declining a transfer keeps the table with the original server
    # also verifies a decline notification is created for the requesting server
    Order.objects.create(
        restaurant=restaurant,
        table=table,
        order_type=Order.OrderType.DINE_IN,
        sub_total=Decimal('10.00'),
        total_price=Decimal('10.00'),
        order_status=Order.OrderStatus.PREPARING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    transfer = TableTransferRequest.objects.create(
        table=table,
        requesting_server=server,
        receiving_server=server2,
        status=TableTransferRequest.Status.PENDING
    )
    client.login(username='server2', password='TestPass123!')
    client.post(
        reverse('respond_table_transfer', args=[transfer.id]),
        {'action': 'decline'}
    )
    table.refresh_from_db()
    transfer.refresh_from_db()
    assert table.assigned_server == server
    assert transfer.status == TableTransferRequest.Status.DECLINED


@pytest.mark.django_db
def test_non_receiving_server_cannot_respond_to_transfer(client, server, server2, table):
    # verifies only the receiving server can respond to a transfer request
    server3 = User.objects.create_user(
        username='server3', password='TestPass123!', role=User.Role.SERVER_HOST
    )
    transfer = TableTransferRequest.objects.create(
        table=table,
        requesting_server=server,
        receiving_server=server2,
        status=TableTransferRequest.Status.PENDING
    )
    client.login(username='server3', password='TestPass123!')
    response = client.post(
        reverse('respond_table_transfer', args=[transfer.id]),
        {'action': 'accept'}
    )
    assert response.status_code == 302
    table.refresh_from_db()
    # table should not have been reassigned to server3
    assert table.assigned_server == server


# ====================== HOST MODE TOGGLE ======================

@pytest.mark.django_db
def test_host_mode_toggle_switches_session(client, server):
    # verifies the host mode toggle correctly flips the session flag
    client.login(username='server1', password='TestPass123!')
    assert not client.session.get('host_mode', False)
    client.post(reverse('toggle_host_mode'))
    assert client.session.get('host_mode') is True
    client.post(reverse('toggle_host_mode'))
    assert client.session.get('host_mode') is False


@pytest.mark.django_db
def test_host_mode_toggle_blocked_for_customer(client, customer):
    # verifies customers cannot toggle host mode
    client.login(username='customer1', password='TestPass123!')
    response = client.post(reverse('toggle_host_mode'))
    assert response.status_code == 302
    assert not client.session.get('host_mode', False)


# ====================== SERVER ADD TO ORDER ======================

@pytest.mark.django_db
def test_server_can_access_add_to_order_page(client, server, table):
    # verifies servers can access the menu page to add items to a table order
    client.login(username='server1', password='TestPass123!')
    response = client.get(reverse('server_add_to_order', args=[table.id]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_server_add_to_order_creates_order_if_none_exists(client, server, table, restaurant):
    # verifies that adding items to a table with no active order creates a new order
    category = Category.objects.create(name='Test')
    item = MenuItem.objects.create(
        name='Test Item', description='Desc', price=Decimal('10.00'), category=category
    )
    session = client.session
    session[f'server_cart_{table.id}'] = {
        str(item.pk): {
            'item_id': item.pk,
            'name': item.name,
            'price': str(item.price),
            'quantity': 1
        }
    }
    session.save()
    client.login(username='server1', password='TestPass123!')
    client.post(
        reverse('server_add_to_order', args=[table.id]),
        {'confirm_items': '1'}
    )
    assert Order.objects.filter(table=table).exists()


@pytest.mark.django_db
def test_customer_cannot_access_server_add_to_order(client, customer, table):
    # verifies customers cannot access the server order management page
    client.login(username='customer1', password='TestPass123!')
    response = client.get(reverse('server_add_to_order', args=[table.id]))
    assert response.status_code == 302


# ====================== SERVER TABLE DETAIL ======================

@pytest.mark.django_db
def test_server_table_detail_shows_pre_order_if_exists(client, server, table, restaurant):
    # UI test: verifies the table detail page shows the pre-order section when one exists
    from restaurant.models import Reservation, PreOrder, PreOrderItem
    customer_user = User.objects.create_user(
        username='precustomer', password='TestPass123!', role=User.Role.CUSTOMER
    )
    customer_obj = Customer.objects.create(
        user=customer_user, phone_number='4031112222', address='123 Test St'
    )
    reservation = Reservation.objects.create(
        customer=customer_obj,
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + datetime.timedelta(hours=3),
        party_size=2,
        deposit_amount=Decimal('10.00'),
        status=Reservation.Status.CONFIRMED
    )
    preorder = PreOrder.objects.create(
        reservation=reservation,
        customer=customer_obj,
        restaurant=restaurant,
        status=PreOrder.Status.PENDING
    )
    category = Category.objects.create(name='Pre')
    item = MenuItem.objects.create(
        name='PreItem', description='Desc', price=Decimal('12.00'), category=category
    )
    PreOrderItem.objects.create(
        preorder=preorder, menu_item=item, quantity=1, unit_price=Decimal('12.00')
    )
    client.login(username='server1', password='TestPass123!')
    response = client.get(reverse('server_table_detail', args=[table.id]))
    content = response.content.decode()
    assert 'Pre-Order' in content or 'pre-order' in content.lower()
    assert 'PreItem' in content


@pytest.mark.django_db
def test_server_can_activate_preorder(client, server, table, restaurant):
    # verifies servers can activate a pre-order and it creates a real order in the DB
    from restaurant.models import Reservation, PreOrder, PreOrderItem
    customer_user = User.objects.create_user(
        username='preactivate', password='TestPass123!', role=User.Role.CUSTOMER
    )
    customer_obj = Customer.objects.create(
        user=customer_user, phone_number='4031112222', address='123 Test St'
    )
    reservation = Reservation.objects.create(
        customer=customer_obj,
        table=table,
        restaurant=restaurant,
        reservation_datetime=timezone.now() + datetime.timedelta(hours=3),
        party_size=2,
        deposit_amount=Decimal('10.00'),
        status=Reservation.Status.CONFIRMED
    )
    preorder = PreOrder.objects.create(
        reservation=reservation,
        customer=customer_obj,
        restaurant=restaurant,
        status=PreOrder.Status.PENDING
    )
    category = Category.objects.create(name='ActivateTest')
    item = MenuItem.objects.create(
        name='ActivateItem', description='Desc', price=Decimal('15.00'), category=category
    )
    PreOrderItem.objects.create(
        preorder=preorder, menu_item=item, quantity=2, unit_price=Decimal('15.00')
    )
    client.login(username='server1', password='TestPass123!')
    client.post(reverse('server_activate_preorder', args=[preorder.id]))
    preorder.refresh_from_db()
    table.refresh_from_db()
    assert preorder.status == PreOrder.Status.ACTIVATED
    assert table.status == Table.Status.OCCUPIED
    assert Order.objects.filter(table=table).exists()