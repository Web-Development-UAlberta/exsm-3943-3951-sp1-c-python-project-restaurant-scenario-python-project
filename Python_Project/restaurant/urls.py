from django.urls import path
from . import views

urlpatterns = [

    # ====================== CUSTOMER VIEWS ======================
    path('', views.customer_index, name='index'),
    path('restaurant/customer_login/', views.customer_login, name='customer_login'),
    path('restaurant/user_logout/', views.user_logout, name='user_logout'),
    path('restaurant/customer_signup/', views.customer_signup, name='customer_signup'),
    path('restaurant/customer/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customer/', views.customer_list, name='customer_list'),
    path('customer/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customer/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),

    # ====================== STAFF AUTH ======================
    path('restaurant/staff_index/', views.staff_index, name='staff_index'),
    path('restaurant/staff_login/', views.staff_login, name='staff_login'),
    path('restaurant/staff_signup/', views.staff_signup, name='staff_signup'),

    # ====================== STAFF DASHBOARDS ======================
    path('restaurant/manager/', views.manager_view, name='manager_view'),
    path('restaurant/server/', views.server_host_view, name='server_host_view'),
    path('restaurant/kitchen/', views.kitchen_view, name='kitchen_view'),
    path('restaurant/driver/', views.driver_view, name='driver_view'),
    path('restaurant/owner/', views.owner_view, name='owner_view'),

    # ====================== STAFF MANAGEMENT ======================
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/<int:pk>/', views.staff_detail, name='staff_detail'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),

    # ====================== STAFF INVITES ======================
    path('staff-invites/', views.staff_invite_list, name='staff_invite_list'),
    path('staff-invites/new/', views.staff_invite_create, name='staff_invite_create'),
    path('staff-invites/<int:pk>/delete/', views.staff_invite_delete, name='staff_invite_delete'),

    # ====================== RESTAURANT ======================
    path('restaurant/', views.restaurant_list, name='restaurant_list'),
    path('restaurant/new/', views.restaurant_create, name='restaurant_create'),
    path('restaurant/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('restaurant/<int:pk>/edit/', views.restaurant_edit, name='restaurant_edit'),
    path('restaurant/<int:pk>/toggle/', views.restaurant_toggle_active, name='restaurant_toggle_active'),
    path('restaurant/<int:pk>/delete/', views.restaurant_confirm_delete, name='restaurant_confirm_delete'),

    # ====================== TABLE ======================
    path('restaurant/<int:restaurant_pk>/table/', views.table_list, name='table_list'),
    path('table/<int:pk>/', views.table_detail, name='table_detail'),
    path('restaurant/<int:restaurant_pk>/table/new/', views.table_create, name='table_create'),
    path('table/<int:pk>/edit/', views.table_edit, name='table_edit'),
    path('table/<int:pk>/delete/', views.table_confirm_delete, name='table_confirm_delete'),
    path('table/<int:table_id>/update_status/', views.update_table_status, name='update_table_status'),
    path('table/<int:table_id>/assign_server/', views.assign_server_to_table, name='assign_server_to_table'),
    
    # ====================== TABLE LAYOUT ======================
    path('restaurant/<int:restaurant_pk>/layout/', views.table_layout_edit, name='table_layout_edit'),
    path('restaurant/<int:restaurant_pk>/layout/save/', views.table_layout_save, name='table_layout_save'),

    # ====================== CATEGORY ======================
    path('category/', views.category_list, name='category_list'),
    path('category/<int:pk>/', views.category_detail, name='category_detail'),
    path('category/new/', views.category_create, name='category_create'),
    path('category/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('category/<int:pk>/delete/', views.category_confirm_delete, name='category_confirm_delete'),

    # ====================== TAG ======================
    path('tag/', views.tag_list, name='tag_list'),
    path('tag/<int:pk>/', views.tag_detail, name='tag_detail'),
    path('tag/new/', views.tag_create, name='tag_create'),
    path('tag/<int:pk>/edit/', views.tag_edit, name='tag_edit'),
    path('tag/<int:pk>/delete/', views.tag_confirm_delete, name='tag_confirm_delete'),

    # ====================== MENU ITEM ======================
    path('menu-item/', views.menu_item_list, name='menu_item_list'),
    path('menu-item/<int:pk>/', views.menu_item_detail, name='menu_item_detail'),
    path('menu-item/new/', views.menu_item_create, name='menu_item_create'),
    path('menu-item/<int:pk>/edit/', views.menu_item_edit, name='menu_item_edit'),
    path('menu-item/<int:pk>/delete/', views.menu_item_confirm_delete, name='menu_item_confirm_delete'),

    # ====================== ORDERS ======================
    path('order/', views.order_list, name='order_list'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('order/new/', views.order_create, name='order_create'),
    path('order/<int:pk>/edit/', views.order_edit, name='order_edit'),
    path('order/<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('order/<int:pk>/link/', views.order_link_to_account, name='order_link_to_account'),
    path('orders/<int:order_id>/update_status/', views.update_order_status, name='update_order_status'),

    # ====================== RESERVATIONS ======================
    path('reservation/', views.reservation_list, name='reservation_list'),
    path('reservation/<int:pk>/', views.reservation_detail, name='reservation_detail'),
    path('reservation/new/', views.reservation_create, name='reservation_create'),
    path('reservation/<int:pk>/cancel/', views.reservation_cancel, name='reservation_cancel'),

    # ====================== INVENTORY ======================
    path('restaurant/<int:restaurant_pk>/inventory/', views.inventory_list, name='inventory_list'),
    path('restaurant/<int:restaurant_pk>/inventory/new/', views.inventory_create, name='inventory_create'),
    path('inventory/<int:pk>/edit/', views.inventory_edit, name='inventory_edit'),
    path('inventory/<int:pk>/delete/', views.inventory_confirm_delete, name='inventory_confirm_delete'),
    
    # ====================== Delivery ======================
    path('order/<int:order_id>/assign-driver/', views.assign_driver_to_order, name='assign_driver_to_order'),
    path('order/<int:order_id>/complete-delivery/', views.delivery_complete, name='delivery_complete'),

    # ====================== CART ======================
    path('cart/add/<int:item_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),

    # ====================== REPORTS ======================
    path('reporting/', views.reporting_view, name='reporting_view'),

    # ====================== PAYMENT ======================
    path('order/<int:order_id>/payment/', views.payment_page, name='payment_page'),
    path('order/<int:order_id>/create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('order/<int:order_id>/payment/success/', views.payment_success, name='payment_success'),
    path('order/<int:order_id>/payment/confirmation/', views.payment_confirmation, name='payment_confirmation'),
]