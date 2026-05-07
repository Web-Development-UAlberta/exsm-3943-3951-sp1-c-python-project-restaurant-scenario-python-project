import pytest
from django.urls import reverse
from django.utils import timezone
from restaurant.models import User, Table, Order, Restaurant


# ====================== STAFF BUSINESS LOGIC TESTS ======================

@pytest.mark.django_db
def test_staff_list_access_for_manager(client):
    """Managers can access staff list"""
    manager = User.objects.create_user(
        username='manager1', 
        password='pass123', 
        role=User.Role.MANAGER
    )
    client.login(username='manager1', password='pass123')
    
    response = client.get(reverse('staff_list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_unauthorized_user_cannot_access_staff_list(client):
    """Customers should be blocked from staff management"""
    customer = User.objects.create_user(
        username='cust1', 
        password='pass123', 
        role=User.Role.CUSTOMER
    )
    client.login(username='cust1', password='pass123')
    
    response = client.get(reverse('staff_list'))
    assert response.status_code != 200


@pytest.mark.django_db
def test_manager_can_access_staff_detail(client):
    """Managers can view staff details"""
    manager = User.objects.create_user(username='manager1', password='pass123', role=User.Role.MANAGER)
    staff = User.objects.create_user(username='staff1', password='pass123', role=User.Role.SERVER_HOST)
    
    client.login(username='manager1', password='pass123')
    response = client.get(reverse('staff_detail', args=[staff.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_server_can_update_table_status(client):
    """Server/Host can update table status"""
    restaurant = Restaurant.objects.create(
        name="Test Restaurant",
        address="123 Test St",
        phone_number="403-555-1234",
        opening_time=timezone.now().time(),
        closing_time=timezone.now().time(),
        latitude=52.27,
        longitude=-113.81
    )
    
    table = Table.objects.create(
        label="T5", 
        seats=4, 
        grid_squares={"x": 0, "y": 0}, 
        status=Table.Status.AVAILABLE, 
        restaurant=restaurant
    )
    
    server = User.objects.create_user(
        username='server1', 
        password='pass123', 
        role=User.Role.SERVER_HOST
    )
    client.login(username='server1', password='pass123')
    
    response = client.post(
        reverse('update_table_status', args=[table.id]),
        {'status': Table.Status.OCCUPIED.value}
    )
    
    assert response.status_code == 302
    table.refresh_from_db()
    assert table.status == Table.Status.OCCUPIED


@pytest.mark.django_db
def test_kitchen_can_update_order_status(client):
    """Kitchen staff can update order status"""
    order = Order.objects.create(
        order_type=Order.OrderType.DINE_IN,
        sub_total=45.50,
        total_price=45.50,
        order_status=Order.OrderStatus.PENDING,
        payment_status=Order.PaymentStatus.UNPAID
    )
    
    kitchen = User.objects.create_user(
        username='kitchen1', 
        password='pass123', 
        role=User.Role.KITCHEN_STAFF
    )
    client.login(username='kitchen1', password='pass123')
    
    response = client.post(
        reverse('update_order_status', args=[order.id]),
        {'status': Order.OrderStatus.PREPARING.value}
    )
    
    assert response.status_code == 302
    order.refresh_from_db()
    assert order.order_status == Order.OrderStatus.PREPARING


@pytest.mark.django_db
def test_server_can_assign_server_to_table(client):
    """Server/Host can assign a server to a table"""
    restaurant = Restaurant.objects.create(
        name="Test Restaurant",
        address="123 Test St",
        phone_number="403-555-1234",
        opening_time=timezone.now().time(),
        closing_time=timezone.now().time(),
        latitude=52.27,
        longitude=-113.81
    )
    
    table = Table.objects.create(
        label="T5", 
        seats=4, 
        grid_squares={"x": 0, "y": 0}, 
        status=Table.Status.AVAILABLE, 
        restaurant=restaurant
    )
    
    server = User.objects.create_user(
        username='server1', 
        password='pass123', 
        role=User.Role.SERVER_HOST
    )
    client.login(username='server1', password='pass123')
    
    response = client.post(
        reverse('assign_server_to_table', args=[table.id]),
        {'server_id': server.id}
    )
    
    assert response.status_code == 302


@pytest.mark.django_db
def test_unauthorized_user_cannot_update_table_status(client):
    """Security test: Customer cannot update table status"""
    restaurant = Restaurant.objects.create(
        name="Test", address="Addr", phone_number="123",
        opening_time=timezone.now().time(), closing_time=timezone.now().time(),
        latitude=0, longitude=0
    )
    table = Table.objects.create(
        label="T1", 
        seats=4, 
        grid_squares={"x": 0, "y": 0}, 
        restaurant=restaurant
    )
    
    customer = User.objects.create_user(username='cust', password='pass', role=User.Role.CUSTOMER)
    client.login(username='cust', password='pass')
    
    response = client.post(reverse('update_table_status', args=[table.id]), {'status': 2})
    
    assert response.status_code == 302
    table.refresh_from_db()
    assert table.status == Table.Status.AVAILABLE  # unchanged