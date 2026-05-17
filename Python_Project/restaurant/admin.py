from django.contrib import admin
from restaurant.models import (
    User, Customer, Restaurant, Table, TableLayout,
    Category, Tag, MenuItem, RestaurantMenuItem, MenuItemTag,
    Reservation, Order, OrderItem, Payment,
    Inventory, StaffInvite
)

admin.site.register(User)
admin.site.register(Customer)
admin.site.register(Restaurant)
admin.site.register(Table)
admin.site.register(TableLayout)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(MenuItem)
admin.site.register(RestaurantMenuItem)
admin.site.register(MenuItemTag)
admin.site.register(Reservation)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Inventory)
admin.site.register(StaffInvite)