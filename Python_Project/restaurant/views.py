from django.shortcuts import render, get_object_or_404, redirect
from restaurant import models
from django.contrib.auth import login as auth_login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from restaurant import forms
from django.urls import reverse
from django.db.models import Q, F
from django.utils import timezone
from .utils import haversine_distance, geocode_address


# ====================== CONSISTENT ROLE HELPERS ======================

def is_manager_or_owner(user):
    """Managers and Owners have full staff management rights"""
    return user.role in [models.User.Role.MANAGER, models.User.Role.OWNER]


def is_server_or_manager(user):
    """Server/Host + Manager/Owner can manage tables"""
    return user.role in [models.User.Role.SERVER_HOST, models.User.Role.MANAGER, models.User.Role.OWNER]


def is_kitchen_or_manager(user):
    """Kitchen Staff + Manager/Owner can manage orders"""
    return user.role in [models.User.Role.KITCHEN_STAFF, models.User.Role.MANAGER, models.User.Role.OWNER]


def is_driver_or_manager(user):
    """Delivery Driver + Manager/Owner"""
    return user.role in [models.User.Role.DELIVERY_DRIVER, models.User.Role.MANAGER, models.User.Role.OWNER]

def is_owner(user):
    """Only owners can create restaurants"""
    return user.role == models.User.Role.OWNER


# ====================== EXISTING VIEWS ======================


def restaurant_list(request):
    restaurants = models.Restaurant.objects.all()
    return render(request, 'restaurant/restaurant_list.html', {'restaurants': restaurants})


def restaurant_detail(request, pk):
    restaurant = get_object_or_404(models.Restaurant, pk=pk)
    return render(request, 'restaurant/restaurant_detail.html', {'restaurant': restaurant})

@login_required
@user_passes_test(is_owner)
def restaurant_create(request):
    if request.method == 'POST':
        form = forms.RestaurantForm(request.POST)
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.user = request.user
            restaurant.save()
            return redirect('restaurant_list')
    else:
        form = forms.RestaurantForm()
    return render(request, 'restaurant/restaurant_create.html', {'form': form})

@login_required
@user_passes_test(is_manager_or_owner)
def restaurant_edit(request, pk):
    restaurant = get_object_or_404(models.Restaurant, pk=pk)
    if request.method == 'POST':
        form = forms.RestaurantForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            return redirect('restaurant_list')
    else:
        form = forms.RestaurantForm(instance=restaurant)
    return render(request, 'restaurant/restaurant_create.html', {'form': form})

@login_required
@user_passes_test(is_owner)
def restaurant_confirm_delete(request, pk):
    restaurant = get_object_or_404(models.Restaurant, pk=pk)
    if request.method == 'POST':
        restaurant.delete()
        return redirect('restaurant_list')
    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Restaurant',
        'object_display': restaurant.name,
        'cancel_url': reverse('restaurant_list'),
        'delete_url': request.path
    })

@login_required
@user_passes_test(is_manager_or_owner)
def restaurant_toggle_active(request, pk):
    restaurant = get_object_or_404(models.Restaurant, pk=pk)
    restaurant.is_active = not restaurant.is_active
    restaurant.save()
    messages.success(request, f'{restaurant.name} has been {"deactivated" if not restaurant.is_active else "activated"}.')
    return redirect('restaurant_detail', pk=pk)


# ====================== CUSTOMER VIEWS ======================

# View to display the homepage for customers
def customer_index(request):
    return render(request, 'restaurant/customer_index.html')


# View to log out any user and redirect to homepage
def user_logout(request):
    logout(request)
    return redirect('index')


# View to log in customers
def customer_login(request):
    if 'next' in request.GET:
        messages.warning(request, 'You need to Login first to access this page!')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Login Successful!')
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password!')
    return render(request, 'restaurant/customer_login.html')


# View to create a new customer account and their linked Customer profile
def customer_signup(request):
    if request.method == 'POST':
        form = forms.CustomerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.role = 5
            user.save()
            models.Customer.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
                address=form.cleaned_data['address']
            )
            return redirect('customer_login')
    else:
        form = forms.CustomerSignUpForm()
    return render(request, 'restaurant/customer_signup.html', {'form': form})


def staff_index(request):
    return render(request, 'restaurant/staff_index.html')


# View to edit a customer
@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(models.Customer, pk=pk)
    
    # checks logged in user owns this customer profile, unless they're a manager or owner
    if customer.user != request.user and not is_manager_or_owner(request.user):
        messages.error(request, 'You can only edit your own profile.')
        return redirect('index')

    if request.method == 'POST':
        customer_form = forms.CustomerEditForm(request.POST, instance=customer)

        if customer_form.is_valid():
            customer = customer_form.save(commit=False)
            customer.user.first_name = customer_form.cleaned_data['first_name']
            customer.user.last_name = customer_form.cleaned_data['last_name']
            customer.user.email = customer_form.cleaned_data['email']

            # only update password if provided
            password = customer_form.cleaned_data.get('password1')
            if password:
                customer.user.set_password(password)

            customer.user.save()
            customer.save()
            messages.success(request, f"{customer.user.first_name}'s profile updated successfully!")
            return redirect('index')

    else:
        # passing in user fields explicitly as they live on User not Customer
        customer_form = forms.CustomerEditForm(instance=customer, initial={
            'first_name': customer.user.first_name,
            'last_name': customer.user.last_name,
            'email': customer.user.email
        })

    return render(request, 'restaurant/customer_signup.html', {'customer_form': customer_form})


# View to list all customers — manager/owner only
@login_required
@user_passes_test(is_manager_or_owner)
def customer_list(request):
    customers = models.Customer.objects.all().order_by('user__last_name')
    return render(request, 'restaurant/customer_list.html', {'customers': customers})


# View to see a specific customer's details — manager/owner only
@login_required
@user_passes_test(is_manager_or_owner)
def customer_detail(request, pk):
    customer = get_object_or_404(models.Customer, pk=pk)
    # pulling the customer's order history as well
    orders = models.Order.objects.filter(customer=customer).order_by('-created_at')
    return render(request, 'restaurant/customer_detail.html', {
        'customer': customer,
        'orders': orders
    })


# View to delete a customer — manager/owner only
@login_required
@user_passes_test(is_manager_or_owner)
def customer_delete(request, pk):
    customer = get_object_or_404(models.Customer, pk=pk)
    if request.method == 'POST':
        # deleting the user will cascade and delete the customer record as well
        customer.user.delete()
        messages.success(request, 'Customer account deleted successfully.')
        return redirect('customer_list')
    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Customer',
        'object_display': f'{customer.user.first_name} {customer.user.last_name}',
        'cancel_url': reverse('customer_detail', args=[customer.pk]),
        'delete_url': request.path
    })

# ====================== STAFF AUTH VIEWS ======================

# View to login staff members
def staff_login(request):
    if 'next' in request.GET:
        messages.warning(request, 'You need to Login first to access this page!')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.role == models.User.Role.CUSTOMER:
                messages.error(request, 'Invalid username or password!')
            else:
                auth_login(request, user)
                messages.success(request, 'Login Successful!')
                if user.role == models.User.Role.MANAGER:
                    return redirect('manager_view')
                elif user.role == models.User.Role.SERVER_HOST:
                    return redirect('server_host_view')
                elif user.role == models.User.Role.KITCHEN_STAFF:
                    return redirect('kitchen_view')
                elif user.role == models.User.Role.DELIVERY_DRIVER:
                    return redirect('driver_view')
                elif user.role == models.User.Role.OWNER:
                    return redirect('owner_view')
                else:
                    return redirect('staff_index')
        else:
            messages.error(request, 'Invalid username or password!')
    return render(request, 'restaurant/staff_login.html')


# View to sign up a staff member, checks StaffInvite table before allowing registration
def staff_signup(request):
    if request.method == 'POST':
        form = forms.StaffSignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            invite = models.StaffInvite.objects.filter(email=email, is_used=False).first()
            if not invite:
                messages.error(request, 'This email has not been approved for staff registration.')
            else:
                user = form.save(commit=False)
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.role = invite.role
                user.save()
                invite.is_used = True
                invite.save()
                return redirect('staff_login')
    else:
        form = forms.StaffSignUpForm()
    return render(request, 'restaurant/staff_signup.html', {'form': form})


# ====================== STAFF DASHBOARDS ======================


# View for the Manager dashboard
@login_required
@user_passes_test(is_manager_or_owner)
def manager_view(request):
    """Manager Dashboard"""
    return render(request, 'restaurant/manager_view.html')


# View for the Server/Host dashboard, shows all tables with assigned server info
@login_required
@user_passes_test(is_server_or_manager)
def server_host_view(request):
    """Server/Host Dashboard - Now includes assigned servers"""
    tables = models.Table.objects.all().order_by('label').select_related('assigned_server')
    context = {'tables': tables}
    return render(request, 'restaurant/server_host_view.html', context)


# View for the Kitchen dashboard
@login_required
@user_passes_test(is_kitchen_or_manager)
def kitchen_view(request):
    """Kitchen Dashboard"""
    orders = models.Order.objects.filter(
        order_status__in=[models.Order.OrderStatus.PENDING, models.Order.OrderStatus.PREPARING]
    ).order_by('created_at')
    context = {'orders': orders}
    return render(request, 'restaurant/kitchen_view.html', context)





# View for the Owner dashboard
@login_required
@user_passes_test(is_manager_or_owner)
def owner_view(request):
    """Owner Dashboard"""
    return render(request, 'restaurant/owner_view.html')


# ====================== STAFF BUSINESS LOGIC ======================

# View to list all staff members
@login_required
@user_passes_test(is_manager_or_owner)
def staff_list(request):
    """List all staff members with shift info and status"""
    staff_members = models.User.objects.exclude(role=models.User.Role.CUSTOMER).order_by('role', 'first_name')
    context = {
        'staff_members': staff_members,
        'total_staff': staff_members.count()
    }
    return render(request, 'restaurant/staff_list.html', context)


# View to see a specific staff member's details and their assigned orders
@login_required
@user_passes_test(is_manager_or_owner)
def staff_detail(request, pk):
    """Detailed view of individual staff member + assigned orders"""
    staff = get_object_or_404(models.User, pk=pk)
    assigned_orders = models.Order.objects.filter(
        Q(assigned_server=staff) | Q(assigned_driver=staff)
    ).order_by('-created_at')
    context = {
        'staff': staff,
        'assigned_orders': assigned_orders,
    }
    return render(request, 'restaurant/staff_detail.html', context)


# ====================== SERVER TO TABLE ASSIGNMENT ======================


@login_required
@user_passes_test(is_server_or_manager)
def assign_server_to_table(request, table_id):
    """Assign a server to a specific table"""
    table = get_object_or_404(models.Table, id=table_id)

    if request.method == 'POST':
        server_id = request.POST.get('server_id')
        server = get_object_or_404(
            models.User,
            id=server_id,
            role=models.User.Role.SERVER_HOST
        )

        # === SAVE THE ASSIGNMENT ===
        table.assigned_server = server
        table.save()

        messages.success(
            request,
            f"Server {server.get_full_name() or server.username} assigned to Table {table.label}"
        )
        return redirect('server_host_view')

    # GET request - show form
    available_servers = models.User.objects.filter(
        role=models.User.Role.SERVER_HOST,
        is_active_staff=True
    )

    context = {
        'table': table,
        'servers': available_servers,
    }
    return render(request, 'restaurant/assign_server_to_table.html', context)


# ====================== TABLE & ORDER MANAGEMENT ======================


@login_required
@user_passes_test(is_server_or_manager)
def update_table_status(request, table_id):
    """Server/Host can update table status"""
    table = get_object_or_404(models.Table, id=table_id)

    if request.method == 'POST':
        new_status = int(request.POST.get('status'))
        table.status = new_status
        table.save()
        messages.success(request, f'Table {table.label} status updated to {table.get_status_display()}')
        return redirect('server_host_view')

    context = {
        'table': table,
        'status_choices': models.Table.Status.choices,
    }
    return render(request, 'restaurant/update_table_status.html', context)


@login_required
@user_passes_test(is_kitchen_or_manager)
def update_order_status(request, order_id):
    """Kitchen Staff can update order status"""
    order = get_object_or_404(models.Order, id=order_id)

    if request.method == 'POST':
        new_status = int(request.POST.get('status'))
        order.order_status = new_status

        # award loyalty points when order is marked as completed
        if new_status == models.Order.OrderStatus.COMPLETED and order.customer:
            points_to_award = int(order.sub_total) * 10  # 10 points per dollar, excluding tax
            order.points_earned = points_to_award
            order.customer.loyalty_points += points_to_award
            order.customer.save()
        
        order.save()
        messages.success(request, f'Order #{order.id} status updated to {order.get_order_status_display()}')
        return redirect('kitchen_view')

    context = {
        'order': order,
        'status_choices': models.Order.OrderStatus.choices,
    }
    return render(request, 'restaurant/update_order_status.html', context)


#========= CATEGORY VIEWS ========

def category_list(request):
    categories = models.Category.objects.all()
    return render(request, 'restaurant/category_list.html', {'categories': categories})


def category_detail(request, pk):
    category = get_object_or_404(models.Category, pk=pk)
    return render(request, 'restaurant/category_detail.html', {'category': category})


@login_required
@user_passes_test(is_manager_or_owner)
def category_create(request):
    if request.method == 'POST':
        form = forms.CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = forms.CategoryForm()
    return render(request, 'restaurant/category_create.html', {'form': form})


@login_required
@user_passes_test(is_manager_or_owner)
def category_edit(request, pk):
    category = get_object_or_404(models.Category, pk=pk)
    if request.method == 'POST':
        form = forms.CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = forms.CategoryForm(instance=category)
    return render(request, 'restaurant/category_create.html', {'form': form})


@login_required
@user_passes_test(is_manager_or_owner)
def category_confirm_delete(request, pk):
    category = get_object_or_404(models.Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Category',
        'object_display': category.name,
        'cancel_url': reverse('category_list'),
        'delete_url': request.path
    })


#========= TAG VIEWS ========

def tag_list(request):
    tags = models.Tag.objects.all()
    return render(request, 'restaurant/tag_list.html', {'tags': tags})


def tag_detail(request, pk):
    tag = get_object_or_404(models.Tag, pk=pk)
    return render(request, 'restaurant/tag_detail.html', {'tag': tag})


@login_required
@user_passes_test(is_manager_or_owner)
def tag_create(request):
    if request.method == 'POST':
        form = forms.TagForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tag_list')
    else:
        form = forms.TagForm()
    return render(request, 'restaurant/tag_create.html', {'form': form})


@login_required
@user_passes_test(is_manager_or_owner)
def tag_edit(request, pk):
    tag = get_object_or_404(models.Tag, pk=pk)
    if request.method == 'POST':
        form = forms.TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            return redirect('tag_list')
    else:
        form = forms.TagForm(instance=tag)
    return render(request, 'restaurant/tag_create.html', {'form': form})


@login_required
@user_passes_test(is_manager_or_owner)
def tag_confirm_delete(request, pk):
    tag = get_object_or_404(models.Tag, pk=pk)
    if request.method == 'POST':
        tag.delete()
        return redirect('tag_list')
    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Tag',
        'object_display': tag.name,
        'cancel_url': reverse('tag_list'),
        'delete_url': request.path
    })


#=========== TABLE VIEWS ==========

def table_list(request, restaurant_pk):
    """takes in restaurant_pk as context identifier for referencing tables belonging to specific restaurant"""
    restaurant = get_object_or_404(models.Restaurant, pk=restaurant_pk)
    tables = models.Table.objects.filter(restaurant=restaurant)
    return render(request, 'restaurant/table_list.html', {'tables': tables, 'restaurant': restaurant})


def table_detail(request, pk):
    table = get_object_or_404(models.Table, pk=pk)
    return render(request, 'restaurant/table_detail.html', {'table': table})


@login_required
@user_passes_test(is_manager_or_owner)
def table_create(request, restaurant_pk):
    restaurant = get_object_or_404(models.Restaurant, pk=restaurant_pk) # grabs pk of restaurant and assigns it during table add
    if request.method == 'POST':
        form = forms.TableForm(request.POST)
        if form.is_valid():
            table = form.save(commit=False) # builds object but doesn't save yet
            table.restaurant = restaurant # pulled from restaurant_pk
            table.grid_squares = []
            table.save() # will write to database now with the update
            return redirect('table_list', restaurant_pk=restaurant.pk)
    else:
        form = forms.TableForm()
    return render(request, 'restaurant/table_create.html', {'form': form})


@login_required
@user_passes_test(is_manager_or_owner)
def table_edit(request, pk):
    table = get_object_or_404(models.Table, pk=pk)
    if request.method == 'POST':
        form = forms.TableForm(request.POST, instance=table)
        if form.is_valid():
            form.save()
            return redirect('table_list', restaurant_pk=table.restaurant.pk)
    else:
        form = forms.TableForm(instance=table)
    return render(request, 'restaurant/table_create.html', {'form': form})


@login_required
@user_passes_test(is_manager_or_owner)
def table_confirm_delete(request, pk):
    table = get_object_or_404(models.Table, pk=pk)
    if request.method == 'POST':
        restaurant_pk = table.restaurant.pk
        table.delete()
        return redirect('table_list', restaurant_pk=restaurant_pk)
    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Table',
        'object_display': table.label,
        'cancel_url': reverse('table_list', kwargs={'restaurant_pk': table.restaurant.pk}),
        'delete_url': request.path
    })


#======= Menu Item =======

def menu_item_list(request):
    menuitems = models.MenuItem.objects.all()
    return render(request, 'restaurant/menu_item_list.html', {'menuitems': menuitems})


def menu_item_detail(request, pk):
    menuitem = get_object_or_404(models.MenuItem, pk=pk)
    return render(request, 'restaurant/menu_item_detail.html', {'menuitem': menuitem})


@login_required
@user_passes_test(is_manager_or_owner)
def menu_item_create(request):
    if request.method == 'POST':
        form = forms.MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('menu_item_list')
    else:
        form = forms.MenuItemForm()
    return render(request, 'restaurant/menu_item_create.html', {'form': form})


@login_required
@user_passes_test(is_manager_or_owner)
def menu_item_edit(request, pk):
    menuitem = get_object_or_404(models.MenuItem, pk=pk)
    if request.method == 'POST':
        form = forms.MenuItemForm(request.POST, request.FILES, instance=menuitem)
        if form.is_valid():
            form.save()
            return redirect('menu_item_list')
    else:
        form = forms.MenuItemForm(instance=menuitem)
    return render(request, 'restaurant/menu_item_create.html', {'form': form})


@login_required
@user_passes_test(is_manager_or_owner)
def menu_item_confirm_delete(request, pk):
    menuitem = get_object_or_404(models.MenuItem, pk=pk)
    if request.method == 'POST':
        menuitem.delete()
        return redirect('menu_item_list')
    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'MenuItem',
        'object_display': menuitem.name,
        'cancel_url': reverse('menu_item_list'),
        'delete_url': request.path
    })


#=======Orders=======#

# View to get all the orders
def order_list(request):
    # customers see only their own orders, staff see all orders, guests see session order
    if request.user.is_authenticated:
        if request.user.role == models.User.Role.CUSTOMER:
            customer = get_object_or_404(models.Customer, user=request.user)
            orders = models.Order.objects.filter(customer=customer)
        else:
            orders = models.Order.objects.all()
    else:
        guest_order_id = request.session.get('guest_order_id')
        if guest_order_id:
            orders = models.Order.objects.filter(id=guest_order_id)
        else:
            orders = models.Order.objects.none()

    return render(request, 'restaurant/order_list.html', {'orders': orders})


# View to get specific order details
def order_detail(request, pk):
    order = get_object_or_404(models.Order, pk=pk)
    return render(request, 'restaurant/order_detail.html', {'order': order})


# View to place an order
def order_create(request):
    # both guests and logged in customers can place an order
    if request.method == 'POST':
        form = forms.OrderForm(request.POST)

        if form.is_valid():
            order = form.save(commit=False)
            order.sub_total = 0 # this will be calculated when the items are added
            order.total_price = 0
            order.loyalty_discount = 0
            
            # validate delivery distance
            if order.order_type == models.Order.OrderType.DELIVERY:
                delivery_address = form.cleaned_data.get('delivery_address')
                coords = geocode_address(delivery_address)
                
                # calls geocode_address function from utils.py and sends delivery address to Nominatim to get coordinates.  Returns None if fails
                if coords is None:
                    messages.error(request, 'Could not verify delivery address.  Please check your address and try again.')
                    return render(request, 'restaurant/order_form.html', {'form':form})
                
                # coordinates are returned as tuple.  delivery lat and lon get unpakced take restaurant object and calculate distance between them 
                delivery_lat, delivery_long = coords
                restaurant = models.Restaurant.objects.filter(is_active=True).first()
                if restaurant is None:
                    messages.error(request, 'No active restaurant found.')
                    return render(request, 'restaurant/order_form.html', {'form':form})
                distance = haversine_distance(restaurant.latitude, restaurant.longitude, delivery_lat, delivery_long)
                
                # display message for over 10km delivery address distance and formats to 1 decimal place.
                if distance > 10:
                    messages.error(request, f"Sorry, your address is {distance:.1f}km away. We only deliver within 10km.")
                    return render(request, 'restaurant/order_form.html', {'form': form})

            # linking the order to the customer if logged in
            if request.user.is_authenticated and request.user.role == models.User.Role.CUSTOMER:
                customer = get_object_or_404(models.Customer, user=request.user)
                order.customer = customer

                # handling loyalty points redemption
                redeem = form.cleaned_data.get('redeem_points')
                if redeem == 'True': # that means the customer wants to redeem points
                    points = customer.loyalty_points
                    if points >= 2000:
                        order.loyalty_discount = 25
                        order.points_redeemed = 2000
                        customer.loyalty_points -= 2000
                    elif points >= 1000:
                        order.loyalty_discount = 10
                        order.points_redeemed = 1000
                        customer.loyalty_points -= 1000
                    else:
                        messages.warning(request, 'You need at least 1000 points to redeem a discount.')

                    customer.save()

            # if it is a guest order, no customer linked
            else:
                order.customer = None

            # calculating the delivery fee based on the order type
            if order.order_type == models.Order.OrderType.DELIVERY:
                order.delivery_fee = 10 # flat $10 delivery fee
            else:
                order.delivery_fee = None

            order.save()

            # storing order id in session so guests can manage their orders
            if not request.user.is_authenticated:
                request.session['guest_order_id'] = order.id

            messages.success(request, f'Order #{order.id} placed successfully!')
            return redirect('order_detail', pk=order.pk)

    else:
        # if the user is not submitting the form, that means they are requesting the form
        # pre-filling the form with delivery address if the customer is logged in
        initial_address = {}
        if request.user.is_authenticated and request.user.role == models.User.Role.CUSTOMER:
            try:
                customer = models.Customer.objects.get(user=request.user)
                initial_address['delivery_address'] = customer.address
            except models.Customer.DoesNotExist:
                pass

        form = forms.OrderForm(initial=initial_address)

    # building context with form and customer object for loyalty points display in template
    context = {'form': form}
    if request.user.is_authenticated and request.user.role == models.User.Role.CUSTOMER:
        try:
            context['customer'] = models.Customer.objects.get(user=request.user) # passing customer so template can show loyalty points balance
        except models.Customer.DoesNotExist:
            pass # if no customer record exists, template will show 0 pts
    return render(request, 'restaurant/order_form.html', context)


# View to edit orders - only available for logged in customers
@login_required
def order_edit(request, pk):
    # only logged in customers can edit their own orders and only if the order status is still 'pending'
    order = get_object_or_404(models.Order, pk=pk)
    customer = get_object_or_404(models.Customer, user=request.user)

    if order.customer != customer:
        messages.error(request, 'You can only edit your own orders.')
        return redirect('order_list')

    if order.order_status != models.Order.OrderStatus.PENDING:
        messages.error(request, 'You can only edit orders that are still pending.')
        return redirect('order_detail', pk=pk)

    if request.method == 'POST':
        form = forms.OrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)

            # handle loyalty points change on edit
            redeem = form.cleaned_data.get('redeem_points')
            if redeem == 'True' and order.points_redeemed == 0:
                points = customer.loyalty_points
                if points >= 2000:
                    order.loyalty_discount = 25
                    order.points_redeemed = 2000
                    customer.loyalty_points -= 2000
                elif points >= 1000:
                    order.loyalty_discount = 10
                    order.points_redeemed = 1000
                    customer.loyalty_points -= 1000
                else:
                    messages.warning(request, 'You need at least 1000 points to redeem a discount.')
                customer.save()
            elif redeem == 'False' and order.points_redeemed > 0:
                # customer changed mind — refund the points
                customer.loyalty_points += order.points_redeemed
                customer.save()
                order.loyalty_discount = 0
                order.points_redeemed = 0

            order.save()
            messages.success(request, 'Order updated successfully!')
            return redirect('order_detail', pk=pk)
    else:
        form = forms.OrderForm(instance=order, initial={
            'delivery_address': order.delivery_address,
            'redeem_points': str(order.points_redeemed > 0) # converts boolean to string to match POINTS_CHOICES values ('True'/'False')
        })

    # building context with form and customer object for loyalty points display in template
    context = {'form': form}
    if request.user.is_authenticated and request.user.role == models.User.Role.CUSTOMER:
        try:
            context['customer'] = models.Customer.objects.get(user=request.user) # passing customer so template can show current loyalty points balance
        except models.Customer.DoesNotExist:
            pass # if no customer record exists, template will show 0 pts
    return render(request, 'restaurant/order_form.html', context)


# View to delete order
def order_delete(request, pk):
    order = get_object_or_404(models.Order, pk=pk)

    # verify ownership — logged in customer or guest with session
    if request.user.is_authenticated:
        if request.user.role == models.User.Role.CUSTOMER:
            customer = get_object_or_404(models.Customer, user=request.user)
            if order.customer != customer:
                messages.error(request, 'You can only delete your own orders.')
                return redirect('order_list')
    else:
        guest_order_id = request.session.get('guest_order_id')
        if guest_order_id != order.id:
            messages.error(request, 'You do not have permission to delete this order.')
            return redirect('index')

    if request.method == 'POST':
        # refund loyalty points if they were redeemed on this order
        if order.customer and order.points_redeemed > 0:
            order.customer.loyalty_points += order.points_redeemed
            order.customer.save()

        order.delete()

        if not request.user.is_authenticated:
            request.session.pop('guest_order_id', None)

        messages.success(request, 'Order cancelled successfully.')
        return redirect('index')

    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Order',
        'object_display': f'Order #{order.id}',
        'cancel_url': reverse('order_detail', args=[order.pk]),  # reverse() converts the URL name to an actual path e.g. /order/5/ — required since confirm_delete.html uses {{ cancel_url }} not {% url %}
        'delete_url': request.path  # grabs the current URL path e.g. /order/5/delete/ and passes it to the form action so the POST submits back to this same view
    })


# View to allow customers to link their guest order to their account after signing up
@login_required
def order_link_to_account(request, pk):
    order = get_object_or_404(models.Order, pk=pk)
    customer = get_object_or_404(models.Customer, user=request.user)

    if order.customer is not None:
        messages.error(request, 'This order is already linked to an account.')
        return redirect('order_detail', pk=pk)

    guest_order_id = request.session.get('guest_order_id')
    if guest_order_id != order.id:
        messages.error(request, 'You can only link orders you placed as a guest.')
        return redirect('index')

    order.customer = customer
    order.save()
    request.session.pop('guest_order_id', None)
    messages.success(request, 'Order linked to your account successfully!')
    return redirect('order_detail', pk=pk)


#======= Reservation Views =======#

# View to cancel a reservation
def reservation_cancel(request, pk):
    reservation = get_object_or_404(models.Reservation, pk=pk)

    if request.method == 'POST':
        now = timezone.now()
        time_until = reservation.reservation_datetime - now
        hours_until = time_until.total_seconds() / 3600

        # apply $10 cancellation fee if within 3 hours
        if hours_until < 3:
            reservation.cancellation_fee_applied = True

        reservation.status = models.Reservation.Status.CANCELLED
        reservation.save()
        messages.success(request, 'Reservation cancelled.')
        return redirect('reservation_list')

    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Reservation',
        'object_display': f'Reservation #{reservation.id}',
        'cancel_url': reverse('reservation_detail', args=[reservation.pk]),
        'delete_url': request.path
    })


# View to list reservations, customers see their own, staff see all
def reservation_list(request):
    if request.user.is_authenticated:
        if request.user.role == models.User.Role.CUSTOMER:
            customer = get_object_or_404(models.Customer, user=request.user)
            reservations = models.Reservation.objects.filter(customer=customer).order_by('-reservation_datetime')
        else:
            reservations = models.Reservation.objects.all().order_by('-reservation_datetime')
    else:
        reservations = models.Reservation.objects.none()
    return render(request, 'restaurant/reservation_list.html', {'reservations': reservations})


# View to see a specific reservation's details
def reservation_detail(request, pk):
    reservation = get_object_or_404(models.Reservation, pk=pk)
    return render(request, 'restaurant/reservation_detail.html', {'reservation': reservation})


# View to create a new reservation, available to both guests and logged in customers
# checks for conflicting reservations on the same table within the next hour
# validates party size, past datetime, and table capacity
def reservation_create(request):
    if request.method == 'POST':
        form = forms.ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)

            # check for conflicting reservations on the same table
            from django.utils import timezone
            reservation_time = form.cleaned_data['reservation_datetime']
            conflict_window = reservation_time + timezone.timedelta(hours=1)

            conflict = models.Reservation.objects.filter(
                table=reservation.table,
                reservation_datetime__lt=conflict_window,
                reservation_datetime__gte=reservation_time,
                status__in=[
                    models.Reservation.Status.PENDING,
                    models.Reservation.Status.CONFIRMED
                ]
            ).exists()

            if conflict:
                messages.error(request, 'This table is already booked within the next hour. Please choose a different table or time.')
                return render(request, 'restaurant/reservation_form.html', {'form': form})

            # link to customer if logged in, otherwise treat as guest
            if request.user.is_authenticated and request.user.role == models.User.Role.CUSTOMER:
                customer = get_object_or_404(models.Customer, user=request.user)
                reservation.customer = customer
            else:
                reservation.customer = None

            reservation.deposit_amount = 10
            reservation.save()
            messages.success(request, f'Reservation #{reservation.id} confirmed. A $10 deposit is required.')
            return redirect('reservation_detail', pk=reservation.pk)
    else:
        form = forms.ReservationForm()
    return render(request, 'restaurant/reservation_form.html', {'form': form})


#======= Staff Invite (Admin Panel) =======#

# View to list all staff invites
@login_required
@user_passes_test(is_manager_or_owner)
def staff_invite_list(request):
    # shows all staff invites — used and unused
    invites = models.StaffInvite.objects.all().order_by('-created_at')
    return render(request, 'restaurant/staff_invite_list.html', {'invites': invites})


# View to create a new staff invite, manager/owner adds email and role to pre-approve a staff member
@login_required
@user_passes_test(is_manager_or_owner)
def staff_invite_create(request):
    # manager/owner adds an email and role to allow that person to sign up as staff
    if request.method == 'POST':
        form = forms.AddStaffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Invite sent to {form.cleaned_data['email']}.")
            return redirect('staff_invite_list')
    else:
        form = forms.AddStaffForm()
    return render(request, 'restaurant/staff_invite_form.html', {'form': form})


# View to delete a staff invite, manager/owner can revoke an unused invite
@login_required
@user_passes_test(is_manager_or_owner)
def staff_invite_delete(request, pk):
    # manager/owner can revoke an unused invite
    invite = get_object_or_404(models.StaffInvite, pk=pk)
    if request.method == 'POST':
        invite.delete()
        messages.success(request, f"Invite for {invite.email} has been revoked.")
        return redirect('staff_invite_list')
    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Staff Invite',
        'object_display': invite.email,
        'cancel_url': reverse('staff_invite_list'),
        'delete_url': request.path
    })


#======= Inventory =======#

@login_required
@user_passes_test(is_manager_or_owner)
def inventory_list(request, restaurant_pk):
    # managers see all ingredients and their current stock levels for their restaurant
    restaurant = get_object_or_404(models.Restaurant, pk=restaurant_pk)
    inventory = models.Inventory.objects.filter(restaurant=restaurant).order_by('ingredient_name')
    # flag low stock items — anything at or below reorder level
    low_stock = inventory.filter(current_level__lte=F('reorder_level'))
    return render(request, 'restaurant/inventory_list.html', {
        'inventory': inventory,
        'low_stock': low_stock,
        'restaurant': restaurant
    })


@login_required
@user_passes_test(is_manager_or_owner)
def inventory_create(request, restaurant_pk):
    restaurant = get_object_or_404(models.Restaurant, pk=restaurant_pk)
    if request.method == 'POST':
        form = forms.InventoryForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.restaurant = restaurant
            item.save()
            return redirect('inventory_list', restaurant_pk=restaurant.pk)
    else:
        form = forms.InventoryForm()
    return render(request, 'restaurant/inventory_form.html', {'form': form})


@login_required
@user_passes_test(is_manager_or_owner)
def inventory_edit(request, pk):
    item = get_object_or_404(models.Inventory, pk=pk)
    if request.method == 'POST':
        form = forms.InventoryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('inventory_list', restaurant_pk=item.restaurant.pk)
    else:
        form = forms.InventoryForm(instance=item)
    return render(request, 'restaurant/inventory_form.html', {'form': form})


@login_required
@user_passes_test(is_manager_or_owner)
def inventory_confirm_delete(request, pk):
    item = get_object_or_404(models.Inventory, pk=pk)
    if request.method == 'POST':
        restaurant_pk = item.restaurant.pk
        item.delete()
        return redirect('inventory_list', restaurant_pk=restaurant_pk)
    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Ingredient',
        'object_display': item.ingredient_name,
        'cancel_url': reverse('inventory_list', kwargs={'restaurant_pk': item.restaurant.pk}),
        'delete_url': request.path
    })
    
    
# ====================== DELIVERY VIEWS ======================

# View for the Driver dashboard
@login_required
@user_passes_test(is_driver_or_manager)
def driver_view(request):
    """Driver Dashboard shows orders ready for delivery"""
    orders = models.Order.objects.filter(
        assigned_driver = request.user,
        order_type=models.Order.OrderType.DELIVERY,
        order_status=models.Order.OrderStatus.READY
    ).order_by('created_at')
    context = {'orders':orders}
    return render(request, 'restaurant/driver_view.html', context)


@login_required
@user_passes_test(is_driver_or_manager)
def delivery_complete(request, order_id):
    """Driver marks a delivery order as complete"""
    order = get_object_or_404(models.Order, id=order_id)
    
    # ensures the driver is assigned to this specific order
    if order.assigned_driver != request.user and not is_manager_or_owner(request.user):
        messages.error(request, 'You can only complete your own deliveries')
        return redirect('driver_view')
    
    if request.method == 'POST':
        order.order_status = models.Order.OrderStatus.COMPLETED
        order.save()
        messages.success(request, f'Order #{order.id} marked as delivered!')
        return redirect('driver_view')
    
    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Delivery',
        'object_display': f'Order #{order.id}',
        'cancel_url': reverse('driver_view'),
        'delete_url': request.path
    })
    
    
@login_required
@user_passes_test(is_manager_or_owner)
def assign_driver_to_order(request, order_id):
    """Assign a driver to a specific order"""
    order = get_object_or_404(models.Order, id=order_id)

    if request.method == 'POST':
        driver_id = request.POST.get('driver_id')
        driver = get_object_or_404(
            models.User,
            id=driver_id,
            role=models.User.Role.DELIVERY_DRIVER
        )

        # === SAVE THE ASSIGNMENT ===
        order.assigned_driver = driver
        order.save()

        messages.success(
            request,
            f"Driver {driver.get_full_name() or driver.username} assigned to Order #{order.id}"
        )
        return redirect('order_list') # manager redirected to order list view 

    # GET request - show form
    available_drivers = models.User.objects.filter(
        role=models.User.Role.DELIVERY_DRIVER,
        is_active_staff=True
    )

    context = {
        'order': order,
        'available_drivers': available_drivers,
    }
    return render(request, 'restaurant/assign_driver_to_order.html', context)