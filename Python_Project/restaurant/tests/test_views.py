import pytest
from django.urls import reverse
from restaurant import models


# ====================== CATEGORY VIEWS TESTS ======================


@pytest.mark.django_db
def test_manager_can_access_category_create(client):
    """Manager can access category create view"""
    manager = models.User.objects.create_user(
        username = 'manager1',
        password='pass123',
        role=models.User.Role.MANAGER
    )
    client.login(username='manager1', password='pass123')
    
    response = client.get(reverse('category_create'))
    assert response.status_code == 200

   
@pytest.mark.django_db    
def test_staff_cannot_access_category_create(client):
    """Server_Host cannot access category create view"""
    server = models.User.objects.create_user(
        username = 'server1',
        password='pass123',
        role=models.User.Role.SERVER_HOST
    )
    client.login(username='server1', password='pass123')
    
    response = client.get(reverse('category_create'))
    assert response.status_code == 302
 
   
@pytest.mark.django_db
def test_manager_create_category_successfully(client):
    """Manager can create a category successfully and checks if it already exists""" 
    manager = models.User.objects.create_user(
        username = 'manager1',
        password='pass123',
        role=models.User.Role.MANAGER
    )
    client.login(username='manager1', password='pass123')
    
    response = client.post(reverse('category_create'), {'name': 'Test Category'})
    assert response.status_code == 302
    assert models.Category.objects.filter(name='Test Category').exists()
    
    
# ====================== RESTAURANT VIEWS TESTS ======================    

@pytest.mark.django_db
def test_owner_can_access_restaurant_create(client):
    """Owner can access restaurant create view"""
    owner = models.User.objects.create_user(
        username = 'owner1',
        password='pass123',
        role=models.User.Role.OWNER
    )
    client.login(username='owner1', password='pass123')
    
    response = client.get(reverse('restaurant_create'))
    assert response.status_code == 200

   
@pytest.mark.django_db    
def test_manager_cannot_access_restaurant_create(client):
    """Manager cannot access restaurant create view"""
    manager = models.User.objects.create_user(
        username = 'manager1',
        password='pass123',
        role=models.User.Role.MANAGER
    )
    client.login(username='manager1', password='pass123')
    
    response = client.get(reverse('restaurant_create'))
    assert response.status_code == 302
 
   
@pytest.mark.django_db
def test_owner_create_restaurant_successfully(client):
    """Owner can create a restaurant successfully and checks if it already exists""" 
    owner = models.User.objects.create_user(
        username = 'owner1',
        password='pass123',
        role=models.User.Role.OWNER
    )
    client.login(username='owner1', password='pass123')
    
    response = client.post(reverse('restaurant_create'), {
        'name': 'Test Restaurant',
        'address': '123 Test St',
        'phone_number': '780-995-1234',
        'opening_time': '09:00',
        'closing_time': '21:00',
        'latitude': '53.5461',
        'longitude': '-113.4938'
        })
    assert response.status_code == 302
    assert models.Restaurant.objects.filter(name='Test Restaurant').exists()
    
# ====================== TAG VIEWS TESTS ======================    

@pytest.mark.django_db
def test_manager_can_access_tag_create(client):
    """Manager can access tag create view"""
    manager = models.User.objects.create_user(
        username = 'manager1',
        password='pass123',
        role=models.User.Role.MANAGER
    )
    client.login(username='manager1', password='pass123')
    
    response = client.get(reverse('tag_create'))
    assert response.status_code == 200

   
@pytest.mark.django_db    
def test_server_cannot_access_tag_create(client):
    """Server cannot access tag create view"""
    server = models.User.objects.create_user(
        username = 'server1',
        password='pass123',
        role=models.User.Role.SERVER_HOST
    )
    client.login(username='server1', password='pass123')
    
    response = client.get(reverse('tag_create'))
    assert response.status_code == 302
 
   
@pytest.mark.django_db
def test_manager_create_tag_successfully(client):
    """Manager can create a tag successfully and checks if it already exists""" 
    manger = models.User.objects.create_user(
        username = 'manager1',
        password='pass123',
        role=models.User.Role.MANAGER
    )
    client.login(username='manager1', password='pass123')
    
    response = client.post(reverse('tag_create'), {'name': 'Test Tag'})
    assert response.status_code == 302
    assert models.Tag.objects.filter(name='Test Tag').exists()