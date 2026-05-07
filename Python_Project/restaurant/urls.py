from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_index, name='index'),
    path('restaurant/staff_index/', views.staff_index, name='staff_index'),
    path('restaurant/customer_login/', views.customer_login, name='customer_login'),
    path('restaurant/user_logout/', views.user_logout, name='user_logout'),
    path('restaurant/customer_signup/', views.customer_signup, name='customer_signup'),
    path('restaurant/staff_login/', views.staff_login, name='staff_login'),
    path('restaurant/staff_signup/', views.staff_signup, name='staff_signup'),
    path('restaurant/', views.restaurant_list, name='restaurant_list'),
    path('restaurant/new/', views.restaurant_create, name='restaurant_create'),
    path('restaurant/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('restaurant/<int:pk>/edit/', views.restaurant_edit, name='restaurant_edit'),
    path('restaurant/<int:pk>/toggle/', views.restaurant_toggle_active, name='restaurant_toggle_active'),
    path('restaurant/<int:pk>/delete/', views.restaurant_confirm_delete, name='restaurant_confirm_delete'),
    path('restaurant/manager/', views.manager_view, name='manager_view'),
    path('restaurant/server/', views.server_host_view, name='server_host_view'),
    path('restaurant/kitchen/', views.kitchen_view, name='kitchen_view'),
    path('restaurant/driver/', views.driver_view, name='driver_view'),
    path('restaurant/owner/', views.owner_view, name='owner_view'),

    # ====================== STAFF BUSINESS LOGIC ======================
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/<int:pk>/', views.staff_detail, name='staff_detail'),

    # ====================== SERVER/HOST TABLE MANAGEMENT ======================
    path('table/<int:table_id>/update_status/', views.update_table_status, name='update_table_status'),
    path('table/<int:table_id>/assign_server/', views.assign_server_to_table, name='assign_server_to_table'),  # ← New

    # ====================== KITCHEN ORDER MANAGEMENT ======================
    path('orders/<int:order_id>/update_status/', views.update_order_status, name='update_order_status'),
    
       #======== Category ========
       
    path('category/', views.category_list, name='category_list'),
    path('category/<int:pk>/', views.category_detail, name='category_detail'),
    path('category/new/', views.category_create, name='category_create'),
    path('category/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('category/<int:pk>/delete/', views.category_confirm_delete, name='category_confirm_delete'),
    #======== Tag ========
    
    path('tag/', views.tag_list, name='tag_list'),
    path('tag/<int:pk>/', views.tag_detail, name='tag_detail'),
    path('tag/new/', views.tag_create, name='tag_create'),
    path('tag/<int:pk>/edit/', views.tag_edit, name='tag_edit'),
    path('tag/<int:pk>/delete/', views.tag_confirm_delete, name='tag_confirm_delete'),
    #======== Menu Item ========
    
    path('menu-item/', views.menu_item_list, name='menu_item_list'),
    path('menu-item/<int:pk>/', views.menu_item_detail, name='menu_item_detail'),
    path('menu-item/new/', views.menu_item_create, name='menu_item_create'),
    path('menu-item/<int:pk>/edit/', views.menu_item_edit, name='menu_item_edit'),
    path('menu-item/<int:pk>/delete/', views.menu_item_confirm_delete, name='menu_item_confirm_delete'),
]