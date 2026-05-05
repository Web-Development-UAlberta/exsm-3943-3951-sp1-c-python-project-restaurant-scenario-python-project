from django.urls import path
from . import views

urlpatterns = [
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('restaurants/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('restaurants/new/', views.restaurant_create, name='restaurant_create'),
    path('restaurants/<int:pk>/edit/', views.restaurant_edit, name='restaurant_edit'),
    path('restauarnt/<int:pk>/toggle/', views.restaurant_toggle_active, name='restaurant_toggle_active'),
    path('restaurants/<int:pk>/delete/', views.restaurant_confirm_delete, name='restaurant_confirm_delete'),
    
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/<int:pk>/', views.tag_detail, name='tag_detail'),
    path('tags/new/', views.tag_create, name='tag_create'),
    path('tags/<int:pk>/edit/', views.tag_edit, name='tag_edit'),
    
]