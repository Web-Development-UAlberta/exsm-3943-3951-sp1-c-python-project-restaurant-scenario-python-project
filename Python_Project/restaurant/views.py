from django.shortcuts import render, get_object_or_404, redirect
from restaurant import models
from django.contrib.auth import login as auth_login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from restaurant import forms
from django.urls import reverse
from django.db.models import Q, F, Count, Sum
from django.utils import timezone
from .utils import haversine_distance, geocode_address
from django.http import JsonResponse
import json
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.utils.dateparse import parse_datetime


# GST rate applied to all orders
TAX_RATE = Decimal('0.05')


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

def can_access_table_layout(user):
    return user.role in [
        models.User.Role.MANAGER,
        models.User.Role.OWNER,
        models.User.Role.SERVER_HOST,
    ]


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
            # Geocode the address to get lat/lng automatically
            address = form.cleaned_data.get('address')
            coords = geocode_address(address)
            if coords:
                restaurant.latitude = Decimal(str(coords[0]))
                restaurant.longitude = Decimal(str(coords[1]))
            else:
                # Fallback: set to 0 if geocoding fails, owner can update later
                restaurant.latitude = Decimal('0')
                restaurant.longitude = Decimal('0')
                messages.warning(request, 'Could not geocode the address. Coordinates set to 0. You can update them later')
            restaurant.save()
            messages.success(request, f'{restaurant.name} created successfully.')
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
            restaurant = form.save(commit=False)
            # Re-geocode if address changes
            address = form.cleaned_data.get('address')
            coords = geocode_address(address)
            if coords:
                restaurant.latitude = Decimal(str(coords[0]))
                restaurant.longitude = Decimal(str(coords[1]))
            restaurant.save()
            messages.success(request, f'{restaurant.name} updated successfully.')
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
            # block staff from logging in through the customer login page
            # show a warning and redirect them to the staff login page after a short delay
            if user.role != models.User.Role.CUSTOMER:
                messages.warning(request, 'This login is for customers only. Redirecting you to the Staff Login page...')
                return render(request, 'restaurant/customer_login.html', {'redirect_to_staff': True})
            auth_login(request, user)
            messages.success(request, 'Login Successful!')
            return redirect('customer_dashboard')
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
            auth_login(request, user)
            messages.success(request, 'Account created Successfully!')
            return redirect('customer_dashboard')
    else:
        form = forms.CustomerSignUpForm()
    return render(request, 'restaurant/customer_signup.html', {'form': form})


def staff_index(request):
    return render(request, 'restaurant/staff_index.html')


# View to edit a customer
@login_required
def customer_edit(request, pk):
    # block staff from editing customer profiles
    if request.user.role != models.User.Role.CUSTOMER and not is_manager_or_owner(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_index')

    customer = get_object_or_404(models.Customer, pk=pk)

    # Determine where to go back to based on who is editing
    if is_manager_or_owner(request.user):
        back_url = reverse('customer_detail', args=[customer.pk])
    else:
        back_url = reverse('customer_dashboard')
    
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
            # managers and owners go back to customer detail, customers go back to their dashboard
            return redirect(back_url)

    else:
        # passing in user fields explicitly as they live on User not Customer
        customer_form = forms.CustomerEditForm(instance=customer, initial={
            'first_name': customer.user.first_name,
            'last_name': customer.user.last_name,
            'email': customer.user.email
        })

    return render(request, 'restaurant/customer_signup.html', {
            'customer_form': customer_form, 
            'back_url':back_url
        })


# View to list all customers — manager/owner only
@login_required
@user_passes_test(is_manager_or_owner)
def customer_list(request):
    customers = models.Customer.objects.all().order_by('user__last_name')
    # determine back url: owner goest to owner_view, manager goes to manager_view
    if request.user.role == models.User.Role.OWNER:
        back_url = reverse('owner_view')
    else:
        back_url = reverse('manager_view')
    return render(request, 'restaurant/customer_list.html', {'customers': customers, 'back_url':back_url})


# View to see a specific customer's details — manager/owner only
@login_required
@user_passes_test(is_manager_or_owner)
def customer_detail(request, pk):
    # block staff from viewing customer detail pages
    if request.user.role != models.User.Role.CUSTOMER and not is_manager_or_owner(request.user):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_index')

    customer = get_object_or_404(models.Customer, pk=pk)
    # pulling the customer's order history as well
    orders = models.Order.objects.filter(customer=customer).order_by('-created_at')
    
    # determine back url: owner goes to owner_view, manager goes to manager_view
    if request.user.role == models.User.Role.OWNER:
        back_url = reverse('owner_view')
    else:
        back_url = reverse('manager_view')
    return render(request, 'restaurant/customer_detail.html', {
        'customer': customer,
        'orders': orders,
        'back_url': back_url,
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


# View for the customer dashboard, shows loyalty points, upcoming reservations, and recent orders
@login_required
def customer_dashboard(request):
    # only customers can access this dashboard
    if request.user.role != models.User.Role.CUSTOMER:
        return redirect('staff_index')

    customer = get_object_or_404(models.Customer, user=request.user)

    # get upcoming reservations, only pending or confirmed, sorted by soonest first
    upcoming_reservations = models.Reservation.objects.filter(
        customer=customer,
        status__in=[models.Reservation.Status.PENDING, models.Reservation.Status.CONFIRMED],
        reservation_datetime__gte=timezone.now()
    ).order_by('reservation_datetime')[:3]

    # show recent orders regardless of payment status
    # exclude only cancelled orders so the dashboard stays relevant
    recent_orders = models.Order.objects.filter(
        customer=customer,
    ).exclude(
        order_status=models.Order.OrderStatus.CANCELLED
    ).order_by('-created_at')[:5]

    return render(request, 'restaurant/customer_dashboard.html', {
        'customer': customer,
        'upcoming_reservations': upcoming_reservations,
        'recent_orders': recent_orders,
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
    # managers see their own restaurant regardless of active status
    # owners see all restaurants
    if request.user.role == models.User.Role.OWNER:
        restaurants = models.Restaurant.objects.all()
    else:
        restaurants = models.Restaurant.objects.filter(user=request.user)
    return render(request, 'restaurant/manager_view.html', {'restaurants': restaurants})


# View for the Server/Host dashboard, shows all tables with assigned server info
@login_required
@user_passes_test(is_server_or_manager)
def server_host_view(request):
    """Server/Host Dashboard.
        Servers only see tables assigned to them.
        Managers and owners see all tables.
        Includes ready-order notification per table"""
    
    if request.user.role == models.User.Role.SERVER_HOST:
        # cards only show assigned tables, but grid shows all tables in the restaurant
        assigned_tables = models.Table.objects.filter(
            assigned_server=request.user
        ).order_by('label').select_related('assigned_server', 'restaurant')

        # get the restaurant from the first assigned table to scope the full grid
        # if no tables are assigned yet, fall back to all tables
        if assigned_tables.exists():
            restaurant = assigned_tables.first().restaurant
            all_restaurant_tables = models.Table.objects.filter(
                restaurant=restaurant
            ).order_by('label').select_related('assigned_server', 'restaurant')
        else:
            assigned_tables = models.Table.objects.none()
            all_restaurant_tables = models.Table.objects.all().order_by('label').select_related('assigned_server', 'restaurant')

        tables = assigned_tables
        grid_tables = all_restaurant_tables
    else:
        tables = models.Table.objects.all().order_by('label').select_related('assigned_server', 'restaurant')
        grid_tables = tables
    
    # Building per-table notification data: orders at READY status linked to each table
    ready_notifications = models.Notification.objects.filter(
        notification_type__in=[
            models.Notification.NotificationType.ORDER_READY,
            models.Notification.NotificationType.TABLE_ATTENTION,
        ],
        is_read=False,
        table__in=grid_tables
    ).select_related('order', 'table')
    
    # Building a dict of table_id -> list of ready notifications for template use
    notification_by_table = {}
    for n in ready_notifications:
        if n.table_id not in notification_by_table:
            notification_by_table[n.table_id] = []
        notification_by_table[n.table_id].append(n)

    # Enrich table objects with their active order (if any) for actions
    table_data = []
    for table in tables:
        active_order = models.Order.objects.filter(
            table=table,
            order_status__in=[
                models.Order.OrderStatus.PENDING,
                models.Order.OrderStatus.PREPARING,
                models.Order.OrderStatus.READY,
            ]
        ).order_by('-created_at').first()
        table_data.append({
            'table': table,
            'active_order': active_order,
            'notifications': notification_by_table.get(table.id, [])
        })

    # pending transfer requests where this user is the receiving server
    # shown as a separate notification bar above the table cards
    pending_transfers = models.TableTransferRequest.objects.filter(
        receiving_server=request.user,
        status=models.TableTransferRequest.Status.PENDING
    ).select_related('table', 'requesting_server')

    context = {
        'table_data': table_data,
        'tables': tables,
        'grid_tables': grid_tables,
        'pending_transfers': pending_transfers,
    }
    return render(request, 'restaurant/server_host_view.html', context)


# View to dismiss a notification
@login_required
def dismiss_notification(request, notification_id):
    """Mark a server notification as read via POST."""
    notification = get_object_or_404(models.Notification, id=notification_id)
    notification.is_read = True
    notification.save()
    return redirect('server_host_view')


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
    # owners see all restaurants
    restaurants = models.Restaurant.objects.all()
    return render(request, 'restaurant/owner_view.html', {'restaurants': restaurants})


# ====================== STAFF BUSINESS LOGIC ======================

# View to list all staff members
@login_required
@user_passes_test(is_manager_or_owner)
def staff_list(request):
    """List all staff members with shift info and status.
    Owners can filter by restaurant location via query param.
    Location is determined by the restaurant each staff member is linked to
    via their assigned tables."""
    staff_members = models.User.objects.exclude(
        role=models.User.Role.CUSTOMER
    ).order_by('role', 'first_name')

    # managers only see staff at their own restaurant
    # owners see everyone across all locations
    if request.user.role == models.User.Role.MANAGER:
        manager_restaurant = models.Restaurant.objects.filter(user=request.user).first()
        if manager_restaurant:
            # get servers assigned to tables at this restaurant
            servers_at_restaurant = models.Table.objects.filter(
                restaurant=manager_restaurant,
                assigned_server__isnull=False
            ).values_list('assigned_server_id', flat=True)
            # include the manager themselves and their restaurant's servers
            staff_members = staff_members.filter(
                Q(pk__in=servers_at_restaurant) |
                Q(pk=request.user.pk)
            )
        else:
            # manager has no restaurant linked, only show themselves
            staff_members = staff_members.filter(pk=request.user.pk)

    # get all restaurants for the filter dropdown
    # owners see all restaurants in the filter dropdown
    # managers only have one restaurant so no filter is needed
    if request.user.role == models.User.Role.OWNER:
        restaurants = models.Restaurant.objects.all()
    else:
        restaurants = models.Restaurant.objects.none()

    # apply location filter if selected
    selected_restaurant_id = request.GET.get('restaurant_id')
    if selected_restaurant_id:
        # filter staff by tables assigned to the selected restaurant
        staff_at_restaurant = models.Table.objects.filter(
            restaurant__pk=selected_restaurant_id,
            assigned_server__isnull=False
        ).values_list('assigned_server_id', flat=True)
        # also include managers linked to that restaurant
        managers_at_restaurant = models.Restaurant.objects.filter(
            pk=selected_restaurant_id
        ).values_list('user_id', flat=True)
        combined_ids = set(list(staff_at_restaurant) + list(managers_at_restaurant))
        staff_members = staff_members.filter(pk__in=combined_ids)

    if request.user.role == models.User.Role.OWNER:
        back_url = reverse('owner_view')
    else:
        back_url = reverse('manager_view')

    return render(request, 'restaurant/staff_list.html', {
        'staff_members': staff_members,
        'total_staff': staff_members.count(),
        'back_url': back_url,
        'restaurants': restaurants,
        'selected_restaurant_id': selected_restaurant_id,
    })


# View to see a specific staff member's details and their assigned orders
@login_required
@user_passes_test(is_manager_or_owner)
def staff_detail(request, pk):
    """Detailed view of individual staff member + assigned orders"""
    staff = get_object_or_404(models.User, pk=pk)
    assigned_orders = models.Order.objects.filter(
        Q(assigned_server=staff) | Q(assigned_driver=staff)
    ).order_by('-created_at')
    
    if request.user.role == models.User.Role.OWNER:
        back_url = reverse('owner_view')
    else:
        back_url = reverse('manager_view')
    return render(request, 'restaurant/staff_detail.html', {
        'staff': staff,
        'assigned_orders': assigned_orders,
        'back_url': back_url,
    })


# View to edit a staff member: manager/owner only
@login_required
@user_passes_test(is_manager_or_owner)
def staff_edit(request, pk):
    staff = get_object_or_404(models.User, pk=pk)

    # prevent editing customers through this view
    if staff.role == models.User.Role.CUSTOMER:
        messages.error(request, 'Use the customer edit page to edit customers.')
        return redirect('staff_list')

    if request.method == 'POST':
        form = forms.StaffEditForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, f"{staff.get_full_name()}'s profile updated successfully!")
            return redirect('staff_detail', pk=staff.pk)
    else:
        form = forms.StaffEditForm(instance=staff)

    return render(request, 'restaurant/staff_edit.html', {'form': form, 'staff': staff})


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
        
        # if request came from fetch, return JSON instead of redirecting
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'status': table.status,
                'status_display': table.get_status_display()
            })
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
    """
    Kitchen Staff can update order status.
    When a delivery order is marked READY, it is automatically assigned to the
    next available driver using round-robin rotation based on current assignment count.
    The assigned driver receives a notification on their dashboard.
    """
    order = get_object_or_404(models.Order, id=order_id)

    if request.method == 'POST':
        new_status = int(request.POST.get('status'))
        
        # prevent backwards status changes: order can only move forward
        # managers can override this if needed
        if new_status < order.order_status and not is_manager_or_owner(request.user):
            messages.error(request, 'Cannot move order back to a previous status.')
            return redirect('kitchen_view')

        order.order_status = new_status

        # When a delivery order is marked READY, auto-assign to next available driver
        # using round-robin: the driver with the fewest active deliveries gets assigned
        if new_status == models.Order.OrderStatus.READY and order.order_type == models.Order.OrderType.DELIVERY:
            active_drivers = models.User.objects.filter(
                role=models.User.Role.DELIVERY_DRIVER,
                is_active_staff=True
            )
            if active_drivers.exists():
                # count active (READY status) delivery orders per driver
                # the driver with the lowest count gets this order
                from django.db.models import Count
                driver_load = active_drivers.annotate(
                    active_deliveries=Count(
                        'delivered_orders',
                        filter=Q(
                            delivered_orders__order_status=models.Order.OrderStatus.READY,
                            delivered_orders__order_type=models.Order.OrderType.DELIVERY
                        )
                    )
                ).order_by('active_deliveries', 'id')

                assigned_driver = driver_load.first()
                order.assigned_driver = assigned_driver

                # create a notification for the assigned driver
                # notification is linked to the order so the driver can see it on their dashboard
                models.Notification.objects.create(
                    table=order.table,
                    order=order,
                    notification_type=models.Notification.NotificationType.ORDER_READY,
                    message=f'Delivery order #{order.id} has been assigned to you. Please pick up from the kitchen.'
                )

                messages.info(request, f'Order #{order.id} auto-assigned to driver {assigned_driver.get_full_name() or assigned_driver.username}.')

        # When a dine-in order is marked READY, notify the server for that table
        if new_status == models.Order.OrderStatus.READY and order.table:
            models.Notification.objects.create(
                table=order.table,
                order=order,
                notification_type=models.Notification.NotificationType.ORDER_READY,
                message=f'Order #{order.id} at Table {order.table.label} is ready!'
            )

        # only award points if they have not already been awarded for this order
        if new_status == models.Order.OrderStatus.COMPLETED and order.customer and order.points_earned == 0:
            points_to_award = int(order.sub_total) * 10
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
    
    # strip 'T' off table label and sort numerically
    tables = models.Table.objects.filter(restaurant=restaurant).extra(
        select={'label_num': "CAST(SUBSTR(label, 2) AS INTEGER)"}
    ).order_by('label_num')
    
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
        
        # remove table from TableLayout grid_data if it exists
        try:
            layout  = models.TableLayout.objects.get(restaurant=table.restaurant)
            layout.grid_data = [t for t in layout.grid_data if t['table_id'] != table.pk]
            layout.save()
        except models.TableLayout.DoesNotExist:
            pass
        
        table.delete()
        return redirect('table_list', restaurant_pk=restaurant_pk)
    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Table',
        'object_display': table.label,
        'cancel_url': reverse('table_list', kwargs={'restaurant_pk': table.restaurant.pk}),
        'delete_url': request.path
    })
    
#======= Table Layout =======
@login_required
@user_passes_test(can_access_table_layout)
def table_layout_edit(request, restaurant_pk):
    """Display interactive floor plan editor for restaurant.  
    Loads existing table positions and passes them to template for rendering."""
    
    restaurant = get_object_or_404(models.Restaurant, pk=restaurant_pk)
    
    # strip 'T' off table label and sort numerically
    tables = models.Table.objects.filter(restaurant=restaurant).extra(
        select={'label_num': "CAST(SUBSTR(label, 2) AS INTEGER)"}
    ).order_by('label_num')
    
    try:
        layout = models.TableLayout.objects.get(restaurant=restaurant)
        grid_data = layout.grid_data
    except models.TableLayout.DoesNotExist:
        grid_data = []
            
    return render(request, 'restaurant/table_layout_form.html', {
        'restaurant':restaurant,
        'tables': tables,
        'grid_data': grid_data,
        'status_choices': models.Table.Status.choices,
    })
    
@login_required
@user_passes_test(can_access_table_layout)
def table_layout_save(request, restaurant_pk):
    """Receives JSON layout data from the floor plan editor and saves table positions"""
    
    if request.method == 'POST':
        restaurant = get_object_or_404(models.Restaurant, pk=restaurant_pk)
        
        try:
            data = json.loads(request.body) # parses raw JSON from the request body received from fetch
            tables_data = data.get('tables', [])
            
            grid_data = []
            for item in tables_data:
                table = get_object_or_404(models.Table, id=item['table_id'])
                
                #calculate grid size based on seat count
                if table.seats <= 4:
                    w, h = 1, 1
                elif table.seats <= 6:
                    w, h = 2, 1
                else:
                    w, h = 2, 2
                    
                # save position to grid_squares on the table
                table.grid_squares = {
                    'x': item['x'],
                    'y': item['y'],
                    'w': w,
                    'h': h
                }
                table.save()
                
                grid_data.append({
                    'table_id':table.id,
                    'label': table.label,
                    'seats': table.seats,
                    'status': table.status,
                    'x': item['x'],
                    'y': item['y'],
                    'w': w,
                    'h': h
                })
                
                # save overall layout snapshot
            models.TableLayout.objects.update_or_create(
                restaurant=restaurant,
                defaults={
                    'grid_data': grid_data,
                    'uploaded_by': request.user
                }
            )
                
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        
    return JsonResponse({'success':False, 'error': 'Method not allowed'}, status=405)

def table_layout_view(request, restaurant_pk):
    """Read only floor plan view for customers during reservation booking.  
    Accepts datetime query parameter and marks a table if there's conflicting reservation."""
    
    restaurant = get_object_or_404(models.Restaurant, pk=restaurant_pk)
    
    tables = models.Table.objects.filter(restaurant=restaurant).extra(
        select={'label_num': "Cast(SUBSTR(label, 2) AS INTEGER)"}
    ).order_by('label_num')
    
    try:
        layout = models.TableLayout.objects.get(restaurant=restaurant)
        grid_data = layout.grid_data
    except models.TableLayout.DoesNotExist:
        grid_data = []
        
    # check for reservations if datetime was passed
    reserved_table_ids = set()
    datetime_str = request.GET.get('datetime') # reads datetime value form the URL query parameter that passes from the JS
    if datetime_str and grid_data:
        try:
            reservation_time = parse_datetime(datetime_str) # converts string into python datetime onbject for conflict window calcuation
            if reservation_time:
                conflict_window = reservation_time + timezone.timedelta(hours=1)
                conflicting = models.Reservation.objects.filter(
                    restaurant=restaurant,
                    reservation_datetime__lt=conflict_window,
                    reservation_datetime__gte=reservation_time,
                    status__in=[
                        models.Reservation.Status.PENDING,
                        models.Reservation.Status.CONFIRMED,
                    ]
                ).values_list('table_id', flat=True)
                reserved_table_ids = set(conflicting)
        except Exception:
            pass
            
        
    for table in grid_data:
        if table['table_id'] in reserved_table_ids:
            table['status'] = 3 # reserved
        else:
            table['status'] = 1 #available
        
    return render(request, 'restaurant/table_layout_view.html', {
        'restaurant': restaurant,
        'tables': tables,
        'grid_data': grid_data,
        'status_choices': models.Table.Status.choices,
    })

#======= Menu Item =======

def menu_item_list(request):
    menuitems = models.MenuItem.objects.all().select_related('category')
    categories = models.Category.objects.all()
    restaurant_active = models.Restaurant.objects.filter(is_active=True).exists()
    
    # build cart summary
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = 0
    for str_id, item_data in cart.items():
        line_total = float(item_data['price']) * item_data['quantity']
        cart_total += line_total
        cart_items.append({
            'item_id': str_id,
            'name': item_data['name'],
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'line_total': round(line_total, 2)
        })

    # pass active restaurants so the toggle availability button knows which restaurant to scope to
    restaurants = models.Restaurant.objects.filter(is_active=True)

    # build a set of unavailable menu item IDs for this restaurant
    # so the template can grey them out without a per-item DB query
    unavailable_ids = set(
        models.RestaurantMenuItem.objects.filter(
            is_available=False
        ).values_list('menu_item_id', flat=True)
    )

    return render(request, 'restaurant/menu_item_list.html', {
        'menuitems': menuitems,
        'categories': categories,
        'cart_items': cart_items,
        'cart_total': round(cart_total, 2),
        'restaurant_active': restaurant_active,
        'restaurants': restaurants,
        'unavailable_ids': unavailable_ids,
    })


def menu_item_detail(request, pk):
    menuitem = get_object_or_404(models.MenuItem, pk=pk)
    # fetch tags linked to this menu item via the MenuItemTag junction table
    tags = models.MenuItemTag.objects.filter(menu_item=menuitem).select_related('tag')
    return render(request, 'restaurant/menu_item_detail.html', {
        'menuitem': menuitem,
        'tags': tags
    })


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
    # block staff roles from accessing customer order views
    if request.user.is_authenticated and request.user.role not in [
        models.User.Role.CUSTOMER,
        models.User.Role.MANAGER,
        models.User.Role.OWNER
    ]:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_index')

    if request.user.is_authenticated:
        if request.user.role == models.User.Role.CUSTOMER:
            customer = get_object_or_404(models.Customer, user=request.user)
            # Customers see only their paid orders + any pending that are still being processed
            orders = models.Order.objects.filter(customer=customer).exclude(
                    payment_status=models.Order.PaymentStatus.UNPAID,
                    order_status=models.Order.OrderStatus.PENDING
                ).order_by('-created_at')

        else:
            orders = models.Order.objects.all().order_by('-created_at')
    else:
        guest_order_id = request.session.get('guest_order_id')
        if guest_order_id:
            orders = models.Order.objects.filter(id=guest_order_id)
        else:
            orders = models.Order.objects.none()

    if request.user.is_authenticated and is_manager_or_owner(request.user):
        back_url = reverse('owner_view') if request.user.role == models.User.Role.OWNER else reverse('manager_view')
    else:
        back_url = reverse('customer_dashboard') if request.user.is_authenticated else reverse('index')

    return render(request, 'restaurant/order_list.html', {
        'orders': orders,
        'back_url': back_url,
    })


# View to get specific order details
def order_detail(request, pk):
    # block staff roles from accessing customer order views
    if request.user.is_authenticated and request.user.role not in [
        models.User.Role.CUSTOMER,
        models.User.Role.MANAGER,
        models.User.Role.OWNER
    ]:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_index')

    order = get_object_or_404(models.Order, pk=pk)
    return render(request, 'restaurant/order_detail.html', {'order': order})


# Review order page — creates Order and OrderItem records on confirmation.
# Order is only saved AFTER payment intent is created and confirmed.
# Here we save a PENDING/UNPAID order, then redirect to payment.
# The success notification fires only after payment_success.
def order_create(request):
    # block staff roles from accessing customer order views
    if request.user.is_authenticated and request.user.role not in [
        models.User.Role.CUSTOMER,
        models.User.Role.MANAGER,
        models.User.Role.OWNER
    ]:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_index')
    
    # block orders if no active restaurant exists
    restaurant = models.Restaurant.objects.filter(is_active=True).first()
    if restaurant is None:
        messages.error(request, 'No active restaurant available. Orders cannot be placed at this time.')
        return redirect('menu_item_list')

    # if the cart is empty, send them back to the menu
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Your cart is empty. Add some items before checking out.')
        return redirect('menu_item_list')

    # build cart items and calculate subtotal from session data
    cart_items = []
    sub_total = 0
    for str_id, item_data in cart.items():
        line_total = float(item_data['price']) * item_data['quantity']
        sub_total += line_total
        cart_items.append({
            'item_id': item_data['item_id'],
            'name': item_data['name'],
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'line_total': round(line_total, 2)
        })
    sub_total = round(sub_total, 2)

    # get customer object if logged in as customer
    customer = None
    if request.user.is_authenticated and request.user.role == models.User.Role.CUSTOMER:
        customer = get_object_or_404(models.Customer, user=request.user)

    if request.method == 'POST':
        form = forms.OrderForm(request.POST)

        if form.is_valid():
            order = form.save(commit=False)
            order_type = order.order_type
            delivery_address = form.cleaned_data.get('delivery_address')

            # ====== GUEST FIELD VALIDATION ======
            # guests must provide name and phone for all order types
            # delivery guests also need an address (already required by OrderForm clean())
            if not request.user.is_authenticated:
                guest_name = request.POST.get('guest_name', '').strip()
                guest_phone = request.POST.get('guest_phone', '').strip()
                if not guest_name or not guest_phone:
                    messages.error(request, 'Please provide your name and phone number.')
                    return render(request, 'restaurant/order_review.html', {
                        'form': form,
                        'cart_items': cart_items,
                        'sub_total': sub_total,
                        'customer': customer,
                    })

            # ====== DELIVERY DISTANCE VALIDATION ======
            distance = None
            if order_type == models.Order.OrderType.DELIVERY:
                coords = geocode_address(delivery_address)
                if coords is None:
                    messages.error(request, 'Could not verify delivery address. Please check and try again.')
                    return render(request, 'restaurant/order_review.html', {
                        'form': form,
                        'cart_items': cart_items,
                        'sub_total': sub_total,
                        'customer': customer,
                    })
                delivery_lat, delivery_lon = coords
                restaurant = models.Restaurant.objects.filter(is_active=True).first()
                if restaurant is None:
                    messages.error(request, 'No active restaurant found.')
                    return render(request, 'restaurant/order_review.html', {
                        'form': form,
                        'cart_items': cart_items,
                        'sub_total': sub_total,
                        'customer': customer,
                    })
                distance = haversine_distance(
                    float(restaurant.latitude), float(restaurant.longitude),
                    delivery_lat, delivery_lon
                )
                if distance > 10:
                    messages.error(request, f'Sorry, your address is {distance:.1f}km away. We only deliver within 10km.')
                    return render(request, 'restaurant/order_review.html', {
                        'form': form,
                        'cart_items': cart_items,
                        'sub_total': sub_total,
                        'customer': customer,
                    })
                

            # ====== LOYALTY POINTS REDEMPTION ======
            loyalty_discount = 0
            points_redeemed = 0
            if customer:
                redeem = form.cleaned_data.get('redeem_points')
                if redeem == 'True':
                    if customer.loyalty_points >= 2000:
                        loyalty_discount = 25
                        points_redeemed = 2000
                        customer.loyalty_points -= 2000
                    elif customer.loyalty_points >= 1000:
                        loyalty_discount = 10
                        points_redeemed = 1000
                        customer.loyalty_points -= 1000
                    else:
                        messages.warning(request, 'You need at least 1000 points to redeem a discount.')
                    customer.save()

            # ====== DELIVERY FEE ======
            delivery_fee = None
            if order_type == models.Order.OrderType.DELIVERY:
                delivery_fee = 5 if distance and distance <= 5 else 10

            # Tax: 5% GST on (sub_total = loyalty_discount + delivery_fee)
            taxable_amount = sub_total - loyalty_discount + (delivery_fee or 0)
            tax_amount = round(taxable_amount * float(TAX_RATE), 2)

            # ====== TOTAL PRICE ======
            total_price = round(taxable_amount + tax_amount, 2)

            # ====== SAVE ORDER ======
            order.sub_total = sub_total
            order.loyalty_discount = loyalty_discount
            order.points_redeemed = points_redeemed
            order.delivery_fee = delivery_fee
            order.total_price = total_price
            order.payment_status = models.Order.PaymentStatus.UNPAID
            order.order_status = models.Order.OrderStatus.PENDING

            # link to customer or save guest info in special instructions
            if customer:
                order.customer = customer
            else:
                order.customer = None
                guest_name = request.POST.get('guest_name', '').strip()
                guest_phone = request.POST.get('guest_phone', '').strip()
                # store guest contact info in special instructions since we have no guest model on Order
                existing_note = form.cleaned_data.get('special_instruction') or ''
                order.special_instruction = f'Guest: {guest_name} | Phone: {guest_phone}' + (f' | Note: {existing_note}' if existing_note else '')

            order.save()

            # ====== SAVE ORDER ITEMS FROM CART ======
            for item_data in cart_items:
                menu_item = get_object_or_404(models.MenuItem, pk=item_data['item_id'])
                models.OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item_data['quantity'],
                    unit_price=item_data['price']
                )

            # ====== CLEAR CART ======
            request.session.pop('cart', None)
            request.session.modified = True

            # store guest order id in session so guest can track their order
            if not request.user.is_authenticated:
                request.session['guest_order_id'] = order.id

            # Go straight to payment, do NOT show success message here
            return redirect('payment_page', order_id=order.pk)

    else:
        # pre-fill delivery address for logged in customers
        initial = {}
        if customer:
            initial['delivery_address'] = customer.address
        form = forms.OrderForm(initial=initial)

    # Calculate loyalty discount preview for template
    loyalty_discount_preview = Decimal('0')
    if customer:
        if customer.loyalty_points >= 2000:
            loyalty_discount_preview = Decimal('25')
        elif customer.loyalty_points >= 1000:
            loyalty_discount_preview = Decimal('10')

    return render(request, 'restaurant/order_review.html', {
        'form': form,
        'cart_items': cart_items,
        'sub_total': float(sub_total),
        'tax_rate': float(TAX_RATE * 100),
        'customer': customer,
        'loyalty_discount_preview': float(loyalty_discount_preview),
    })

# View to edit orders: only available for logged in customers
@login_required
def order_edit(request, pk):
    # block staff roles from accessing customer order views
    if request.user.is_authenticated and request.user.role not in [
        models.User.Role.CUSTOMER,
        models.User.Role.MANAGER,
        models.User.Role.OWNER
    ]:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_index')

    # only logged in customers can edit their own orders and only if the order status is still 'pending'
    order = get_object_or_404(models.Order, pk=pk)
    
    customer = None
    # Managers and owners can edit any order, customers can only edit their own
    if request.user.role == models.User.Role.CUSTOMER:
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

            # Recalculate tax and total
            delivery_fee = order.delivery_fee or Decimal('0')
            taxable_amount = order.sub_total - order.loyalty_discount + delivery_fee
            order.tax_amount = round(taxable_amount * TAX_RATE, 2)
            order.total_price = round(taxable_amount + order.tax_amount, 2)
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
    # block staff roles from accessing customer order views
    if request.user.is_authenticated and request.user.role not in [
        models.User.Role.CUSTOMER,
        models.User.Role.MANAGER,
        models.User.Role.OWNER
    ]:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_index')

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

    # warn the customer if the order is already paid and preparing
    # a cancellation fee may apply since the kitchen is already working on it
    cancellation_warning = None
    if order.payment_status == models.Order.PaymentStatus.PAID:
        cancellation_warning = 'This order has already been paid and is being prepared. A cancellation fee may apply and a refund will be processed to your original payment method.'

    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Order',
        'object_display': f'Order #{order.id}',
        'cancel_url': reverse('order_detail', args=[order.pk]),
        'delete_url': request.path,
        'cancellation_warning': cancellation_warning,
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
    # block staff roles from accessing customer reservation views
    if request.user.is_authenticated and request.user.role not in [
        models.User.Role.CUSTOMER,
        models.User.Role.MANAGER,
        models.User.Role.OWNER
    ]:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_index')

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
            reservations = models.Reservation.objects.all().select_related(
                'customer__user', 'table', 'restaurant'
            ).order_by('-reservation_datetime')
    else:
        reservations = models.Reservation.objects.none()

    if request.user.is_authenticated and is_manager_or_owner(request.user):
        back_url = reverse('owner_view') if request.user.role == models.User.Role.OWNER else reverse('manager_view')
    else:
        back_url = reverse('customer_dashboard') if request.user.is_authenticated else reverse('index')

    return render(request, 'restaurant/reservation_list.html', {
        'reservations': reservations,
        'back_url': back_url,
        'status_choices': models.Reservation.Status.choices,
    })


# View to see a specific reservation's details
def reservation_detail(request, pk):
    reservation = get_object_or_404(models.Reservation, pk=pk)
    return render(request, 'restaurant/reservation_detail.html', {'reservation': reservation})


# View to update the reservation status
@login_required
@user_passes_test(is_manager_or_owner)
def reservation_update_status(request, pk):
    """Manager/owner can change reservation status directly."""
    reservation = get_object_or_404(models.Reservation, pk=pk)
    if request.method == 'POST':
        new_status = int(request.POST.get('status'))
        reservation.status = new_status
        reservation.save()
        messages.success(request, f'Reservation #{reservation.id} status updated to {reservation.get_status_display()}.')
        return redirect('reservation_list')
    return render(request, 'restaurant/reservation_update_status.html', {
        'reservation': reservation,
        'status_choices': models.Reservation.Status.choices,
    })


# View to create a new reservation, available to both guests and logged in customers
# checks for conflicting reservations on the same table within the next hour
# validates party size, past datetime, and table capacity
def reservation_create(request):
    # block staff roles from accessing customer reservation views
    if request.user.is_authenticated and request.user.role not in [
        models.User.Role.CUSTOMER,
        models.User.Role.MANAGER,
        models.User.Role.OWNER
    ]:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_index')

    if request.method == 'POST':
        form = forms.ReservationForm(request.POST, user=request.user)
        if form.is_valid():
            reservation = form.save(commit=False)

            # block reservations if the restaurant is not active
            if not reservation.restaurant.is_active:
                messages.error(request, f'{reservation.restaurant.name} is currently unavailable for reservations.')
                return render(request, 'restaurant/reservation_form.html', {'form': form})

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
        form = forms.ReservationForm(user=request.user)
    return render(request, 'restaurant/reservation_form.html', {'form': form})


#======= Staff Invite (Admin Panel) =======#

# View to list all staff invites
@login_required
@user_passes_test(is_manager_or_owner)
def staff_invite_list(request):
    # shows all staff invites — used and unused
    invites = models.StaffInvite.objects.all().order_by('-created_at')
    
    if request.user.role == models.User.Role.OWNER:
        back_url = reverse('owner_view')
    else:
        back_url = reverse('manager_view')
    return render(request, 'restaurant/staff_invite_list.html', {
        'invites': invites,
        'back_url': back_url,
    })


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
    restaurant = get_object_or_404(models.Restaurant, pk=restaurant_pk)

    # managers can only view inventory for their own restaurant
    # owners can see any restaurant's inventory
    if request.user.role == models.User.Role.MANAGER and restaurant.user != request.user:
        messages.error(request, 'You can only view inventory for your own restaurant.')
        return redirect('manager_view')

    inventory = models.Inventory.objects.filter(restaurant=restaurant).order_by('ingredient_name')
    low_stock = inventory.filter(current_level__lte=F('reorder_level'))
    
    # back button: owner goes to owner dashboard, manager goes to manager dashboard
    if request.user.role == models.User.Role.OWNER:
        back_url = reverse('owner_view')
    else:
        back_url = reverse('manager_view')

    return render(request, 'restaurant/inventory_list.html', {
        'inventory': inventory,
        'low_stock': low_stock,
        'restaurant': restaurant,
        'back_url': back_url,
    })


@login_required
@user_passes_test(is_manager_or_owner)
def inventory_create(request, restaurant_pk):
    restaurant = get_object_or_404(models.Restaurant, pk=restaurant_pk)

    # managers can only add inventory to their own restaurant
    if request.user.role == models.User.Role.MANAGER and restaurant.user != request.user:
        messages.error(request, 'You can only manage inventory for your own restaurant.')
        return redirect('manager_view')

    if request.method == 'POST':
        form = forms.InventoryForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.restaurant = restaurant
            item.save()
            return redirect('inventory_list', restaurant_pk=restaurant.pk)
    else:
        form = forms.InventoryForm()

    return render(request, 'restaurant/inventory_form.html', {
        'form': form,
        'restaurant': restaurant,
    })


@login_required
@user_passes_test(is_manager_or_owner)
def inventory_edit(request, pk):
    item = get_object_or_404(models.Inventory, pk=pk)

    # managers can only edit inventory for their own restaurant
    if request.user.role == models.User.Role.MANAGER and item.restaurant.user != request.user:
        messages.error(request, 'You can only manage inventory for your own restaurant.')
        return redirect('manager_view')
    
    if request.method == 'POST':
        form = forms.InventoryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('inventory_list', restaurant_pk=item.restaurant.pk)
    else:
        form = forms.InventoryForm(instance=item)

    return render(request, 'restaurant/inventory_form.html', {
        'form': form,
        'restaurant': item.restaurant,
    })


@login_required
@user_passes_test(is_manager_or_owner)
def inventory_confirm_delete(request, pk):
    item = get_object_or_404(models.Inventory, pk=pk)

    # managers can only edit inventory for their own restaurant
    if request.user.role == models.User.Role.MANAGER and item.restaurant.user != request.user:
        messages.error(request, 'You can only manage inventory for your own restaurant.')
        return redirect('manager_view')

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
    """
    Driver dashboard.
    Shows new assignments (READY, not yet picked up) separately from
    in-transit orders (picked up, en route) and completed history.
    Drivers are auto-assigned when kitchen marks delivery orders READY.
    """
    # new assignments: READY orders assigned to this driver
    # these need to be acknowledged and picked up
    new_assignments = models.Order.objects.filter(
        assigned_driver=request.user,
        order_type=models.Order.OrderType.DELIVERY,
        order_status=models.Order.OrderStatus.READY
    ).order_by('created_at')

    # completed delivery history
    completed_orders = models.Order.objects.filter(
        assigned_driver=request.user,
        order_type=models.Order.OrderType.DELIVERY,
        order_status=models.Order.OrderStatus.COMPLETED
    ).order_by('-created_at')

    # unread driver notifications
    driver_notifications = models.Notification.objects.filter(
        order__assigned_driver=request.user,
        is_read=False,
        notification_type=models.Notification.NotificationType.ORDER_READY
    ).select_related('order').order_by('-created_at')

    return render(request, 'restaurant/driver_view.html', {
        'orders': new_assignments,
        'completed_orders': completed_orders,
        'driver_notifications': driver_notifications,
    })


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
        # Award loyalty points on delivery completion
        if order.customer and order.points_earned == 0:
            points = int(order.sub_total) * 10
            order.points_earned = points
            order.save()
            order.customer.loyalty_points += points
            order.customer.save()
        messages.success(request, f'Order #{order.id} marked as delivered!')
        return redirect('driver_view')
    
    # GET: show a proper delivery confirmation page (not the generic confirm_delete)
    return render(request, 'restaurant/delivery_confirm.html', {'order': order})


@login_required
@user_passes_test(is_driver_or_manager)
def confirm_pickup(request, order_id):
    """
    Driver confirms they have picked up the order from the kitchen.
    This does not mark the order as completed — that happens on delivery_complete.
    Reuses delivery_confirm.html but with pickup-specific messaging.
    Dismisses the assignment notification once confirmed.
    """
    order = get_object_or_404(models.Order, id=order_id)

    if order.assigned_driver != request.user and not is_manager_or_owner(request.user):
        messages.error(request, 'You can only confirm your own pickups.')
        return redirect('driver_view')

    if request.method == 'POST':
        # mark all assignment notifications for this order as read
        models.Notification.objects.filter(
            order=order,
            notification_type=models.Notification.NotificationType.ORDER_READY
        ).update(is_read=True)

        messages.success(request, f'Order #{order.id} picked up. Head to {order.delivery_address}.')
        return redirect('driver_view')

    # reuse delivery_confirm.html — pass a flag so the template can change the button label
    return render(request, 'restaurant/delivery_confirm.html', {
        'order': order,
        'is_pickup': True,
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



#======= Cart Views =======#

# View to add an item to the cart — works for both guests and logged in customers
# cart is stored in the session as a dictionary keyed by item_id (as string)
def cart_add(request, item_id):
    item = get_object_or_404(models.MenuItem, pk=item_id)
    cart = request.session.get('cart', {})

    str_id = str(item_id)  # session keys must be strings
    if str_id in cart:
        cart[str_id]['quantity'] += 1
    else:
        cart[str_id] = {
            'item_id': item_id,
            'name': item.name,
            'price': str(item.price),  # Decimal not JSON serializable, converting to string to avoid the error
            'quantity': 1
        }

    request.session['cart'] = cart
    request.session.modified = True  # tells Django the session has changed and needs to be saved
    messages.success(request, f'{item.name} added to cart.')
    return redirect(request.META.get('HTTP_REFERER', 'menu_item_list'))  # redirect back to where the user came from to preserve scroll position


# View to remove an item from the cart entirely
def cart_remove(request, item_id):
    cart = request.session.get('cart', {})
    str_id = str(item_id)
    if str_id in cart:
        del cart[str_id]
    request.session['cart'] = cart
    request.session.modified = True
    return redirect(request.META.get('HTTP_REFERER', 'menu_item_list'))


# View to update the quantity of an item in the cart
# if quantity is set to 0 or less, the item is removed from the cart entirely
def cart_update(request, item_id):
    cart = request.session.get('cart', {})
    str_id = str(item_id)
    quantity = int(request.POST.get('quantity', 1))
    if str_id in cart:
        if quantity <= 0:
            del cart[str_id]
        else:
            cart[str_id]['quantity'] = quantity
    request.session['cart'] = cart
    request.session.modified = True
    return redirect(request.META.get('HTTP_REFERER', 'menu_item_list'))


#======= Reporting Views =======#

# View for reporting dashboard for managers and owners
# Managers only see their restaurant
# Owners can select any active restaurant from a drop down menu
@login_required
@user_passes_test(is_manager_or_owner)
def reporting_view(request):
    restaurants = models.Restaurant.objects.filter(is_active=True)

    # Owners can switch between restaurants via dropdown
    # Managers are automatically scoped to their own restaurant via the user FK on Restaurant
    restaurant_id = request.GET.get('restaurant_id')

    if request.user.role == models.User.Role.OWNER:
        if restaurant_id:
            restaurant = get_object_or_404(models.Restaurant, pk=restaurant_id, is_active=True)

        else:
            restaurant = restaurants.first()

    else:
        # manager: pull the restaurant they are linked to directly
        restaurant = get_object_or_404(models.Restaurant, user=request.user, is_active=True)

    
    if restaurant is None:
        messages.error(request, 'No active restaurant found.')

    # ====== FILTERS ======
    category_id = request.GET.get('category')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    sort_by = request.GET.get('sort', 'times_ordered')  # default sort is times ordered

    # ====== REPORT 1: MENU ITEM POPULARITY ======
    # base queryset, scoped to this restaurant, exclude cancelled orders
    popularity = models.OrderItem.objects.filter(
        order__restaurant=restaurant
    ).exclude(
        order__order_status=models.Order.OrderStatus.CANCELLED
    ).values(
        'menu_item__id',
        'menu_item__name',
        'menu_item__category__name',
        'menu_item__category__id'
    ).annotate(
        times_ordered=Count('id'),
        total_revenue=Sum('unit_price')
    )

    # apply category filter if selected
    if category_id:
        popularity = popularity.filter(menu_item__category__id=category_id)

    # apply date range filters if provided
    if date_from:
        popularity = popularity.filter(order__created_at__date__gte=date_from)
    if date_to:
        popularity = popularity.filter(order__created_at__date__lte=date_to)

    # apply sort
    if sort_by == 'revenue':
        popularity = popularity.order_by('-total_revenue')
    elif sort_by == 'name':
        popularity = popularity.order_by('menu_item__name')
    else:
        popularity = popularity.order_by('-times_ordered')

    # ====== REPORT 2: CURRENT INVENTORY STATUS ======
    inventory_items = models.Inventory.objects.filter(
        restaurant=restaurant
    ).order_by('ingredient_name')

    # flag low stock items, current level at or below reorder level
    low_stock = inventory_items.filter(
        current_level__lte=F('reorder_level')
    )

    # get all categories for the filter dropdown
    categories = models.Category.objects.all()

    return render(request, 'restaurant/reporting_view.html', {
        'restaurant': restaurant,
        'restaurants': restaurants,
        'popularity': popularity,
        'inventory_items': inventory_items,
        'low_stock': low_stock,
        'categories': categories,
        'selected_category': category_id,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
    })

# ====================== PAYMENT VIEWS ======================

# View for the payment page — works for both logged in customers and guests
# no @login_required here because guests need to be able to pay too
def payment_page(request, order_id):
    order = get_object_or_404(models.Order, id=order_id)

    # if logged in as customer, verify they own this order
    if request.user.is_authenticated and request.user.role == models.User.Role.CUSTOMER:
        customer = get_object_or_404(models.Customer, user=request.user)
        if order.customer != customer:
            messages.error(request, 'You do not have permission to pay for this order.')
            return redirect('order_list')

    # if guest, verify they own this order via the session
    # works the same way as order_delete — checks guest_order_id in session
    elif not request.user.is_authenticated:
        guest_order_id = request.session.get('guest_order_id')
        if guest_order_id != order.id:
            messages.error(request, 'You do not have permission to pay for this order.')
            return redirect('index')

    # do not allow payment if order is already paid
    if order.payment_status == models.Order.PaymentStatus.PAID:
        messages.info(request, 'This order has already been paid.')
        return redirect('order_detail', pk=order_id)

    # pass the publishable key to the template so Stripe JS can initialize
    # the publishable key is safe to expose in HTML, unlike the secret key
    return render(request, 'restaurant/payment.html', {
        'order': order,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


# View that creates a Stripe PaymentIntent and returns the client secret to the frontend
# called silently by Stripe JS when the customer clicks Pay
# @csrf_exempt because Stripe JS sends a fetch request without Django's CSRF cookie
@csrf_exempt
def create_payment_intent(request, order_id):
    order = get_object_or_404(models.Order, id=order_id)

    if request.method == 'POST':
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY

            # Stripe works in cents so multiply total by 100
            # $28.98 becomes 2898 cents
            amount_in_cents = int(order.total_price * 100)

            # create the payment intent on Stripe's servers
            # metadata stores order info for reference in the Stripe dashboard
            intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency='cad',
                # automatic_payment_methods causes the "automatic payment methods" error
                # we only accept card so we specify explicitly
                payment_method_types=['card'],
                metadata={
                    'order_id': order.id,
                    'restaurant': str(order.restaurant),
                }
            )

            # return the client secret to the frontend so Stripe JS can confirm the payment
            return JsonResponse({'clientSecret': intent.client_secret})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


# View that handles the redirect after Stripe confirms the payment
# Stripe sends the customer back here with the payment_intent id in the query string
def payment_success(request, order_id):
    order = get_object_or_404(models.Order, id=order_id)
    payment_intent_id = request.GET.get('payment_intent')

    if not payment_intent_id:
        messages.error(request, 'Payment confirmation failed.')
        return redirect('order_detail', pk=order_id)

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # verify the payment actually succeeded by checking with Stripe directly
        # we never trust the redirect alone, someone could manually type the success URL
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if intent.status == 'succeeded':
            # update order payment status to paid
            order.payment_status = models.Order.PaymentStatus.PAID
            # Move order to PREPARING now that payment is confirmed
            order.order_status = models.Order.OrderStatus.PREPARING
            order.save()

            # create a Payment record in our database with the Stripe transaction id
            # this satisfies the transaction_id field on the Payment model
            models.Payment.objects.get_or_create(
                transaction_id=payment_intent_id,
                defaults={
                    'order': order,
                    'method': models.Payment.PaymentMethod.CREDIT_CARD,
                    'amount': order.total_price,
                    'status': 'succeeded',
                }
            )

            # Success message fires HERE, after payment confirmed
            messages.success(request, f'Payment successful! Order #{order.id} is confirmed.')
            return redirect('payment_confirmation', order_id=order_id)
        else:
            # Payment failed: mark order as cancelled and save transaction
            order.order_status = models.Order.OrderStatus.CANCELLED
            order.save()
            models.Payment.objects.get_or_create(
                transaction_id=payment_intent_id,
                defaults={
                    'order': order,
                    'method': models.Payment.PaymentMethod.CREDIT_CARD,
                    'amount': order.total_price,
                    'status': 'failed',
                }
            )
            messages.error(request, 'Payment was not successful. Your order has been cancelled.')
            return redirect('order_detail', pk=order_id)

    except Exception as e:
        messages.error(request, f'Payment verification failed: {str(e)}')

    return redirect('order_detail', pk=order_id)


# View that shows the confirmation page after a successful payment
def payment_confirmation(request, order_id):
    order = get_object_or_404(models.Order, id=order_id)
    # get the most recent payment record for this order
    payment = models.Payment.objects.filter(order=order).last()
    return render(request, 'restaurant/payment_confirmation.html', {
        'order': order,
        'payment': payment,
    })


# ====================== PRE-ORDER VIEWS ======================

@login_required
def reservation_preorder_prompt(request, reservation_pk):
    """
    Shown after a reservation is confirmed.
    Asks the customer if they want to pre-order their meal.
    Accessible any time before the reservation date via reservation detail.
    Once the customer arrives (reservation status COMPLETED), this is blocked.
    """
    reservation = get_object_or_404(models.Reservation, pk=reservation_pk)

    # only the customer who owns this reservation can pre-order
    if request.user.role == models.User.Role.CUSTOMER:
        customer = get_object_or_404(models.Customer, user=request.user)
        if reservation.customer != customer:
            messages.error(request, 'You can only pre-order for your own reservations.')
            return redirect('reservation_list')

    # block pre-ordering if the reservation is already completed or cancelled
    if reservation.status in [
        models.Reservation.Status.COMPLETED,
        models.Reservation.Status.CANCELLED
    ]:
        messages.error(request, 'Pre-ordering is no longer available for this reservation.')
        return redirect('reservation_detail', pk=reservation_pk)

    # check if a pre-order already exists for this reservation
    existing_preorder = models.PreOrder.objects.filter(
        reservation=reservation
    ).first()

    return render(request, 'restaurant/reservation_preorder_prompt.html', {
        'reservation': reservation,
        'existing_preorder': existing_preorder,
    })


@login_required
def preorder_menu(request, reservation_pk):
    """
    Menu view for adding items to a pre-order.
    Works like the regular menu but items go into a pre-order session cart
    keyed separately from the main cart so they do not conflict.
    On confirm, a PreOrder and PreOrderItems are created linked to the reservation.
    """
    reservation = get_object_or_404(models.Reservation, pk=reservation_pk)

    # block if reservation is completed or cancelled
    if reservation.status in [
        models.Reservation.Status.COMPLETED,
        models.Reservation.Status.CANCELLED
    ]:
        messages.error(request, 'Pre-ordering is no longer available for this reservation.')
        return redirect('reservation_detail', pk=reservation_pk)

    menuitems = models.MenuItem.objects.all().select_related('category')
    categories = models.Category.objects.all()

    # pre-order uses its own session key so it does not interfere with the regular cart
    preorder_cart = request.session.get(f'preorder_cart_{reservation_pk}', {})
    cart_items = []
    cart_total = 0
    for str_id, item_data in preorder_cart.items():
        line_total = float(item_data['price']) * item_data['quantity']
        cart_total += line_total
        cart_items.append({
            'item_id': str_id,
            'name': item_data['name'],
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'line_total': round(line_total, 2)
        })

    if request.method == 'POST' and 'confirm_preorder' in request.POST:
        if not cart_items:
            messages.error(request, 'Add at least one item before confirming.')
            return render(request, 'restaurant/preorder_menu.html', {
                'reservation': reservation,
                'menuitems': menuitems,
                'categories': categories,
                'cart_items': cart_items,
                'cart_total': round(cart_total, 2),
            })

        customer = get_object_or_404(models.Customer, user=request.user)
        special_instruction = request.POST.get('special_instruction', '').strip()

        # create or replace the pre-order for this reservation
        preorder, created = models.PreOrder.objects.get_or_create(
            reservation=reservation,
            defaults={
                'customer': customer,
                'restaurant': reservation.restaurant,
                'special_instruction': special_instruction,
            }
        )
        if not created:
            # replace existing pre-order items if customer is updating their pre-order
            preorder.items.all().delete()
            preorder.special_instruction = special_instruction
            preorder.status = models.PreOrder.Status.PENDING
            preorder.save()

        # save pre-order items from the session cart
        for item_data in cart_items:
            menu_item = get_object_or_404(models.MenuItem, pk=item_data['item_id'])
            models.PreOrderItem.objects.create(
                preorder=preorder,
                menu_item=menu_item,
                quantity=item_data['quantity'],
                unit_price=item_data['price']
            )

        # clear the pre-order session cart after saving
        request.session.pop(f'preorder_cart_{reservation_pk}', None)
        request.session.modified = True

        messages.success(request, 'Pre-order saved! Your items will be ready when you arrive.')
        return redirect('reservation_detail', pk=reservation_pk)

    return render(request, 'restaurant/preorder_menu.html', {
        'reservation': reservation,
        'menuitems': menuitems,
        'categories': categories,
        'cart_items': cart_items,
        'cart_total': round(cart_total, 2),
    })


def preorder_cart_add(request, reservation_pk, item_id):
    """Add an item to the pre-order session cart for this specific reservation."""
    item = get_object_or_404(models.MenuItem, pk=item_id)
    cart_key = f'preorder_cart_{reservation_pk}'
    cart = request.session.get(cart_key, {})
    str_id = str(item_id)
    if str_id in cart:
        cart[str_id]['quantity'] += 1
    else:
        cart[str_id] = {
            'item_id': item_id,
            'name': item.name,
            'price': str(item.price),
            'quantity': 1
        }
    request.session[cart_key] = cart
    request.session.modified = True
    return redirect('preorder_menu', reservation_pk=reservation_pk)


def preorder_cart_remove(request, reservation_pk, item_id):
    """Remove an item from the pre-order session cart."""
    cart_key = f'preorder_cart_{reservation_pk}'
    cart = request.session.get(cart_key, {})
    str_id = str(item_id)
    if str_id in cart:
        del cart[str_id]
    request.session[cart_key] = cart
    request.session.modified = True
    return redirect('preorder_menu', reservation_pk=reservation_pk)


# ====================== SERVER TABLE DETAIL VIEW ======================

@login_required
@user_passes_test(is_server_or_manager)
def server_table_detail(request, table_id):
    """
    Detailed view for a single table from the server dashboard.
    Shows current status, active order items, pre-order if available,
    and all action buttons: add items, activate pre-order, pay now, transfer.
    Also shows the floor plan grid in read-only mode below the card summary.
    """
    table = get_object_or_404(models.Table, id=table_id)

    # get the active order on this table if one exists
    active_order = models.Order.objects.filter(
        table=table,
        order_status__in=[
            models.Order.OrderStatus.PENDING,
            models.Order.OrderStatus.PREPARING,
            models.Order.OrderStatus.READY,
        ]
    ).prefetch_related('orderitem_set__menu_item').order_by('-created_at').first()

    # get the active confirmed reservation for this table if one exists
    active_reservation = models.Reservation.objects.filter(
        table=table,
        status__in=[
            models.Reservation.Status.PENDING,
            models.Reservation.Status.CONFIRMED
        ]
    ).select_related('customer__user').order_by('reservation_datetime').first()

    # get the pre-order linked to the active reservation if it exists and has not been activated yet
    preorder = None
    if active_reservation:
        preorder = models.PreOrder.objects.filter(
            reservation=active_reservation,
            status=models.PreOrder.Status.PENDING
        ).prefetch_related('items__menu_item').first()

    # get all unread transfer requests incoming to this server for this table
    incoming_transfer = models.TableTransferRequest.objects.filter(
        table=table,
        receiving_server=request.user,
        status=models.TableTransferRequest.Status.PENDING
    ).first()

    # get the floor plan grid for the restaurant so we can render it read-only
    layout = None
    try:
        layout = models.TableLayout.objects.get(restaurant=table.restaurant)
    except models.TableLayout.DoesNotExist:
        pass

    # get all tables for this restaurant to colour-code them on the grid
    all_tables = models.Table.objects.filter(
        restaurant=table.restaurant
    ).values('id', 'label', 'status', 'grid_squares')

    # get unread decline notifications for transfer requests made by this server
    declined_transfers = models.TableTransferRequest.objects.filter(
        requesting_server=request.user,
        table=table,
        status=models.TableTransferRequest.Status.DECLINED
    )

    return render(request, 'restaurant/server_table_detail.html', {
        'table': table,
        'active_order': active_order,
        'active_reservation': active_reservation,
        'preorder': preorder,
        'incoming_transfer': incoming_transfer,
        'declined_transfers': declined_transfers,
        'layout': layout,
        'all_tables': list(all_tables),
        'status_choices': models.Table.Status.choices,
    })


@login_required
@user_passes_test(is_server_or_manager)
def server_activate_preorder(request, preorder_id):
    """
    Server activates a pre-order once the customer is seated.
    This creates a real Order and OrderItems from the PreOrder data,
    sends it to the kitchen as PREPARING, and marks the table as OCCUPIED.
    """
    preorder = get_object_or_404(models.PreOrder, id=preorder_id)

    if request.method == 'POST':
        # create the real order from the pre-order
        sub_total = sum(
            item.unit_price * item.quantity
            for item in preorder.items.all()
        )
        from decimal import Decimal as D
        tax_amount = round(sub_total * D('0.05'), 2)
        total_price = sub_total + tax_amount

        order = models.Order.objects.create(
            customer=preorder.customer,
            restaurant=preorder.restaurant,
            reservation=preorder.reservation,
            table=preorder.reservation.table,
            order_type=models.Order.OrderType.DINE_IN,
            sub_total=sub_total,
            tax_amount=tax_amount,
            total_price=total_price,
            special_instruction=preorder.special_instruction,
            payment_status=models.Order.PaymentStatus.UNPAID,
            order_status=models.Order.OrderStatus.PREPARING,
            assigned_server=request.user,
        )

        # create order items from pre-order items
        for item in preorder.items.all():
            models.OrderItem.objects.create(
                order=order,
                menu_item=item.menu_item,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )

        # mark the pre-order as activated so it does not show again
        preorder.status = models.PreOrder.Status.ACTIVATED
        preorder.save()

        # mark the table as occupied now that the customer is seated
        table = preorder.reservation.table
        if table:
            table.status = models.Table.Status.OCCUPIED
            table.save()

        # mark the reservation as confirmed now that they are seated
        preorder.reservation.status = models.Reservation.Status.CONFIRMED
        preorder.reservation.save()

        messages.success(request, f'Pre-order activated! Order #{order.id} sent to the kitchen.')
        return redirect('server_table_detail', table_id=table.id)

    return redirect('server_host_view')


@login_required
@user_passes_test(is_server_or_manager)
def server_add_to_order(request, table_id):
    """
    Server-facing menu view for adding items to the active order on a table.
    Items selected here are appended to the existing order and a notification
    is sent to the kitchen. After confirming, the server is redirected back
    to the table detail view they came from.
    """
    table = get_object_or_404(models.Table, id=table_id)

    # get the active order on this table
    active_order = models.Order.objects.filter(
        table=table,
        order_status__in=[
            models.Order.OrderStatus.PENDING,
            models.Order.OrderStatus.PREPARING,
        ]
    ).order_by('-created_at').first()

    # if no active order exists, create one
    if not active_order:
        active_order = models.Order.objects.create(
            restaurant=table.restaurant,
            table=table,
            order_type=models.Order.OrderType.DINE_IN,
            sub_total=Decimal('0'),
            tax_amount=Decimal('0'),
            total_price=Decimal('0'),
            payment_status=models.Order.PaymentStatus.UNPAID,
            order_status=models.Order.OrderStatus.PENDING,
            assigned_server=request.user,
        )

    menuitems = models.MenuItem.objects.all().select_related('category')
    categories = models.Category.objects.all()

    # use a table-specific cart key so it does not interfere with customer cart
    cart_key = f'server_cart_{table_id}'
    cart = request.session.get(cart_key, {})
    cart_items = []
    cart_total = 0
    for str_id, item_data in cart.items():
        line_total = float(item_data['price']) * item_data['quantity']
        cart_total += line_total
        cart_items.append({
            'item_id': str_id,
            'name': item_data['name'],
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'line_total': round(line_total, 2)
        })

    if request.method == 'POST' and 'confirm_items' in request.POST:
        if not cart_items:
            messages.error(request, 'Add at least one item before confirming.')
        else:
            # append new items to the existing order
            for item_data in cart_items:
                menu_item = get_object_or_404(models.MenuItem, pk=item_data['item_id'])
                # if the item already exists on the order, increase quantity
                existing = models.OrderItem.objects.filter(
                    order=active_order,
                    menu_item=menu_item
                ).first()
                if existing:
                    existing.quantity += item_data['quantity']
                    existing.save()
                else:
                    models.OrderItem.objects.create(
                        order=active_order,
                        menu_item=menu_item,
                        quantity=item_data['quantity'],
                        unit_price=item_data['price']
                    )

            # recalculate order totals after adding new items
            all_items = models.OrderItem.objects.filter(order=active_order)
            new_sub_total = sum(i.unit_price * i.quantity for i in all_items)
            new_tax = round(new_sub_total * Decimal('0.05'), 2)
            active_order.sub_total = new_sub_total
            active_order.tax_amount = new_tax
            active_order.total_price = new_sub_total + new_tax
            active_order.order_status = models.Order.OrderStatus.PREPARING
            active_order.save()

            # clear the server session cart for this table after saving
            request.session.pop(cart_key, None)
            request.session.modified = True

            messages.success(request, f'Items added to Order #{active_order.id} and sent to kitchen.')
            return redirect('server_table_detail', table_id=table_id)

    return render(request, 'restaurant/server_add_to_order.html', {
        'table': table,
        'active_order': active_order,
        'menuitems': menuitems,
        'categories': categories,
        'cart_items': cart_items,
        'cart_total': round(cart_total, 2),
    })


def server_cart_add(request, table_id, item_id):
    """Add an item to the server-side cart for a specific table."""
    item = get_object_or_404(models.MenuItem, pk=item_id)
    cart_key = f'server_cart_{table_id}'
    cart = request.session.get(cart_key, {})
    str_id = str(item_id)
    if str_id in cart:
        cart[str_id]['quantity'] += 1
    else:
        cart[str_id] = {
            'item_id': item_id,
            'name': item.name,
            'price': str(item.price),
            'quantity': 1
        }
    request.session[cart_key] = cart
    request.session.modified = True
    return redirect('server_add_to_order', table_id=table_id)


def server_cart_remove(request, table_id, item_id):
    """Remove an item from the server-side cart for a specific table."""
    cart_key = f'server_cart_{table_id}'
    cart = request.session.get(cart_key, {})
    str_id = str(item_id)
    if str_id in cart:
        del cart[str_id]
    request.session[cart_key] = cart
    request.session.modified = True
    return redirect('server_add_to_order', table_id=table_id)


# ====================== TABLE TRANSFER VIEWS ======================

@login_required
@user_passes_test(is_server_or_manager)
def request_table_transfer(request, table_id):
    """
    Server requests to transfer a table to another server.
    Creates a TableTransferRequest and notifies the receiving server
    via the Notification model so they see a pending request on their dashboard.
    """
    table = get_object_or_404(models.Table, id=table_id)

    if request.method == 'POST':
        receiving_server_id = request.POST.get('receiving_server_id')
        receiving_server = get_object_or_404(
            models.User,
            id=receiving_server_id,
            role=models.User.Role.SERVER_HOST
        )

        # block duplicate pending requests for the same table
        existing = models.TableTransferRequest.objects.filter(
            table=table,
            requesting_server=request.user,
            status=models.TableTransferRequest.Status.PENDING
        ).first()
        if existing:
            messages.warning(request, 'You already have a pending transfer request for this table.')
            return redirect('server_table_detail', table_id=table_id)

        models.TableTransferRequest.objects.create(
            table=table,
            requesting_server=request.user,
            receiving_server=receiving_server,
            status=models.TableTransferRequest.Status.PENDING
        )

        # create a notification for the receiving server so they see the request
        latest_order = (
            models.Order.objects.filter(table=table).order_by('-created_at').first()
            or models.Order.objects.filter(restaurant=table.restaurant).order_by('-created_at').first()
        )
        if latest_order:
            models.Notification.objects.create(
                table=table,
                order=latest_order,
                notification_type=models.Notification.NotificationType.ORDER_READY,
                message=f'{request.user.get_full_name()} wants to transfer Table {table.label} to you.'
            )

        messages.success(request, f'Transfer request sent to {receiving_server.get_full_name()}.')
        return redirect('server_table_detail', table_id=table_id)

    # get all active servers except the current one
    available_servers = models.User.objects.filter(
        role=models.User.Role.SERVER_HOST,
        is_active_staff=True
    ).exclude(id=request.user.id)

    return render(request, 'restaurant/request_table_transfer.html', {
        'table': table,
        'available_servers': available_servers,
    })


@login_required
@user_passes_test(is_server_or_manager)
def respond_table_transfer(request, transfer_id):
    """
    Receiving server accepts or declines a table transfer request.
    On accept: table is reassigned to the receiving server.
    On decline: table stays with the original server and they get a
    notification that the request was declined.
    """
    transfer = get_object_or_404(models.TableTransferRequest, id=transfer_id)

    # only the receiving server or a manager can respond to this
    if request.user != transfer.receiving_server and not is_manager_or_owner(request.user):
        messages.error(request, 'You do not have permission to respond to this transfer request.')
        return redirect('server_host_view')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'accept':
            # reassign the table to the receiving server
            transfer.table.assigned_server = transfer.receiving_server
            transfer.table.save()
            transfer.status = models.TableTransferRequest.Status.ACCEPTED
            transfer.save()
            messages.success(request, f'You have accepted Table {transfer.table.label}.')

        elif action == 'decline':
            transfer.status = models.TableTransferRequest.Status.DECLINED
            transfer.save()
            # notify the requesting server that their request was declined
            # using a generic notification message since there is no dedicated transfer notification type
            latest_order = models.Order.objects.filter(
                table=transfer.table
            ).order_by('-created_at').first()
            if latest_order:
                models.Notification.objects.create(
                    table=transfer.table,
                    order=latest_order,
                    notification_type=models.Notification.NotificationType.TABLE_ATTENTION,
                    message=f'{transfer.receiving_server.get_full_name()} declined your transfer request for Table {transfer.table.label}.'
                )
            messages.info(request, f'Transfer request for Table {transfer.table.label} declined.')

        return redirect('server_host_view')

    return render(request, 'restaurant/respond_table_transfer.html', {'transfer': transfer})


# ====================== GENERATE BILL / SERVER PAY VIEWS ======================

@login_required
@user_passes_test(is_server_or_manager)
def generate_bill(request, order_id):
    """
    Server-side bill generation view.
    Shows a full bill preview with all items, subtotal, tax, and total.
    The server can optionally enter a customer email to look up loyalty points
    and apply a redemption discount before proceeding to Stripe payment.
    Once paid via Stripe, the server is taken to the print/close page.
    """
    order = get_object_or_404(models.Order, id=order_id)
    order_items = models.OrderItem.objects.filter(order=order).select_related('menu_item')

    # look up customer by email if provided — used for loyalty points
    loyalty_customer = None
    loyalty_discount_applied = Decimal('0')

    if request.method == 'POST' and 'lookup_email' in request.POST:
        email = request.POST.get('customer_email', '').strip()
        if email:
            try:
                lookup_user = models.User.objects.get(email=email, role=models.User.Role.CUSTOMER)
                loyalty_customer = models.Customer.objects.get(user=lookup_user)
                request.session[f'bill_loyalty_customer_{order_id}'] = loyalty_customer.pk
            except (models.User.DoesNotExist, models.Customer.DoesNotExist):
                messages.warning(request, 'No customer found with that email.')

    elif request.method == 'POST' and 'apply_redemption' in request.POST:
        loyalty_customer_pk = request.session.get(f'bill_loyalty_customer_{order_id}')
        if loyalty_customer_pk:
            loyalty_customer = get_object_or_404(models.Customer, pk=loyalty_customer_pk)
            redeem = request.POST.get('redeem_points')
            if redeem == 'yes':
                if loyalty_customer.loyalty_points >= 2000:
                    loyalty_discount_applied = Decimal('25')
                    loyalty_customer.loyalty_points -= 2000
                    order.points_redeemed = 2000
                elif loyalty_customer.loyalty_points >= 1000:
                    loyalty_discount_applied = Decimal('10')
                    loyalty_customer.loyalty_points -= 1000
                    order.points_redeemed = 1000
                loyalty_customer.save()

                # recalculate totals with the discount applied
                taxable = order.sub_total - loyalty_discount_applied
                order.loyalty_discount = loyalty_discount_applied
                order.tax_amount = round(taxable * Decimal('0.05'), 2)
                order.total_price = round(taxable + order.tax_amount, 2)
                order.customer = loyalty_customer
                order.save()

                messages.success(request, f'Loyalty discount of ${loyalty_discount_applied} applied.')
                return redirect('generate_bill', order_id=order_id)

    else:
        # check if a loyalty customer was previously looked up in this session
        loyalty_customer_pk = request.session.get(f'bill_loyalty_customer_{order_id}')
        if loyalty_customer_pk:
            loyalty_customer = models.Customer.objects.filter(pk=loyalty_customer_pk).first()

    return render(request, 'restaurant/generate_bill.html', {
        'order': order,
        'order_items': order_items,
        'loyalty_customer': loyalty_customer,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'table': order.table,
    })


@login_required
@user_passes_test(is_server_or_manager)
def bill_payment_success(request, order_id):
    """
    Called after Stripe confirms payment for a server-generated bill.
    Marks the order as paid, awards loyalty points to the customer if linked,
    and redirects to the print/close page.
    """
    order = get_object_or_404(models.Order, id=order_id)
    payment_intent_id = request.GET.get('payment_intent')

    if not payment_intent_id:
        messages.error(request, 'Payment confirmation failed.')
        return redirect('generate_bill', order_id=order_id)

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if intent.status == 'succeeded':
            order.payment_status = models.Order.PaymentStatus.PAID
            order.order_status = models.Order.OrderStatus.COMPLETED

            # award loyalty points to the linked customer based on subtotal
            if order.customer and order.points_earned == 0:
                points = int(order.sub_total) * 10
                order.points_earned = points
                order.customer.loyalty_points += points
                order.customer.save()

            order.save()

            # save the payment record
            models.Payment.objects.get_or_create(
                transaction_id=payment_intent_id,
                defaults={
                    'order': order,
                    'method': models.Payment.PaymentMethod.CREDIT_CARD,
                    'amount': order.total_price,
                    'status': 'succeeded',
                }
            )

            # clear the loyalty session data for this order
            request.session.pop(f'bill_loyalty_customer_{order_id}', None)

            return redirect('bill_close_table', order_id=order_id)

    except Exception as e:
        messages.error(request, f'Payment verification failed: {str(e)}')

    return redirect('generate_bill', order_id=order_id)


@login_required
@user_passes_test(is_server_or_manager)
def bill_close_table(request, order_id):
    """
    Final page after a successful bill payment.
    Shows a receipt-style summary with option to print.
    Server clicks Close Table which changes table status from OCCUPIED to NEEDS_CLEANING.
    """
    order = get_object_or_404(models.Order, id=order_id)
    order_items = models.OrderItem.objects.filter(order=order).select_related('menu_item')
    payment = models.Payment.objects.filter(order=order).last()

    if request.method == 'POST' and 'close_table' in request.POST:
        if order.table:
            order.table.status = models.Table.Status.NEEDS_CLEANING
            order.table.save()
            messages.success(request, f'Table {order.table.label} marked as Needs Cleaning.')
        return redirect('server_host_view')

    return render(request, 'restaurant/bill_close_table.html', {
        'order': order,
        'order_items': order_items,
        'payment': payment,
    })


# ====================== MANAGER NOTES VIEWS ======================

@login_required
@user_passes_test(is_manager_or_owner)
def manager_note_list(request):
    """List all active notes created by this manager for their restaurant."""
    from django.utils import timezone as tz
    if request.user.role == models.User.Role.OWNER:
        notes = models.ManagerNote.objects.filter(
            expires_at__gt=tz.now()
        ).order_by('-created_at')
    else:
        restaurant = models.Restaurant.objects.filter(user=request.user).first()
        notes = models.ManagerNote.objects.filter(
            restaurant=restaurant,
            expires_at__gt=tz.now()
        ).order_by('-created_at')
    return render(request, 'restaurant/manager_note_list.html', {'notes': notes})


@login_required
@user_passes_test(is_manager_or_owner)
def manager_note_create(request):
    """Manager creates a note targeted at a specific role or all staff."""
    from django.utils import timezone as tz
    import datetime

    if request.user.role == models.User.Role.MANAGER:
        restaurant = models.Restaurant.objects.filter(user=request.user).first()
    else:
        # owners can pick which restaurant the note applies to
        restaurant_id = request.POST.get('restaurant_id') or request.GET.get('restaurant_id')
        restaurant = get_object_or_404(models.Restaurant, pk=restaurant_id) if restaurant_id else models.Restaurant.objects.filter(is_active=True).first()
        if not restaurant:
            messages.error(request, 'No active restaurant found.')
            return redirect('owner_view')

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        target_role = int(request.POST.get('target_role', 0))

        if not message:
            messages.error(request, 'Message cannot be empty.')
        else:
            models.ManagerNote.objects.create(
                restaurant=restaurant,
                created_by=request.user,
                message=message,
                target_role=target_role,
                # note expires 24 hours from now
                expires_at=tz.now() + datetime.timedelta(hours=24)
            )
            messages.success(request, 'Note created. It will be visible for 24 hours.')
            return redirect('manager_view')

    restaurants = models.Restaurant.objects.all() if request.user.role == models.User.Role.OWNER else None

    # show all active notes so manager can edit or delete from the same page
    if request.user.role == models.User.Role.OWNER:
        active_notes = models.ManagerNote.objects.filter(
            expires_at__gt=timezone.now()
        ).order_by('-created_at')
    else:
        active_notes = models.ManagerNote.objects.filter(
            restaurant=restaurant,
            expires_at__gt=timezone.now()
        ).order_by('-created_at')

    return render(request, 'restaurant/manager_note_form.html', {
        'target_choices': models.ManagerNote.TARGET_CHOICES,
        'restaurant': restaurant,
        'restaurants': restaurants,
        'active_notes': active_notes,
    })


@login_required
@user_passes_test(is_manager_or_owner)
def manager_note_edit(request, note_id):
    """Manager edits an existing note."""
    note = get_object_or_404(models.ManagerNote, id=note_id)

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        target_role = int(request.POST.get('target_role', 0))
        if not message:
            messages.error(request, 'Message cannot be empty.')
        else:
            note.message = message
            note.target_role = target_role
            note.save()
            messages.success(request, 'Note updated.')
            return redirect('manager_view')

    return render(request, 'restaurant/manager_note_form.html', {
        'note': note,
        'target_choices': models.ManagerNote.TARGET_CHOICES,
        'restaurant': note.restaurant,
    })


@login_required
@user_passes_test(is_manager_or_owner)
def manager_note_delete(request, note_id):
    """Manager deletes a note before its 24-hour expiry."""
    note = get_object_or_404(models.ManagerNote, id=note_id)
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted.')
        return redirect('manager_view')
    return render(request, 'restaurant/confirm_delete.html', {
        'object_name': 'Manager Note',
        'object_display': note.message[:60],
        'cancel_url': reverse('manager_view'),
        'delete_url': request.path
    })


# ====================== MENU ITEM AVAILABILITY TOGGLE ======================

@login_required
@user_passes_test(is_manager_or_owner)
def toggle_menu_item_availability(request, restaurant_pk, menu_item_pk):
    """
    Manager or owner marks a menu item as available or unavailable
    for a specific restaurant. The item shows as greyed out in the menu
    with a Temporarily Unavailable label when is_available is False.
    """
    restaurant = get_object_or_404(models.Restaurant, pk=restaurant_pk)
    menu_item = get_object_or_404(models.MenuItem, pk=menu_item_pk)
    restaurant_menu_item, created = models.RestaurantMenuItem.objects.get_or_create(
        restaurant=restaurant,
        menu_item=menu_item,
        defaults={'is_available': True}
    )
    if request.method == 'POST':
        restaurant_menu_item.is_available = not restaurant_menu_item.is_available
        restaurant_menu_item.save() 
        status = 'available' if restaurant_menu_item.is_available else 'unavailable'
        messages.success(request, f'{restaurant_menu_item.menu_item.name} marked as {status}.')
        return redirect('menu_item_list')
    return redirect('menu_item_list')


@login_required
@user_passes_test(is_server_or_manager)
def toggle_host_mode(request):
    """
    Toggles the server between Server mode and Host mode for the current session.
    Host mode shows all tables but blocks order-taking actions.
    Server mode shows only assigned tables with full order management.
    """
    if request.method == 'POST':
        current = request.session.get('host_mode', False)
        request.session['host_mode'] = not current
    return redirect('server_host_view')


@login_required
@user_passes_test(is_server_or_manager)
def request_table_attention(request, table_id):
    """
    Host sends a notification to the assigned server that a table needs attention.
    The notification appears on the assigned server's dashboard.
    Only available in host mode since servers manage their own tables directly.
    """
    table = get_object_or_404(models.Table, id=table_id)

    if request.method == 'POST':
        # only send the notification if there is a server assigned to this table
        if table.assigned_server:
            # find the latest order on this table to link the notification to
            latest_order = models.Order.objects.filter(
                table=table
            ).order_by('-created_at').first()

            if latest_order:
                models.Notification.objects.create(
                    table=table,
                    order=latest_order,
                    notification_type=models.Notification.NotificationType.TABLE_ATTENTION,
                    message=f'Table {table.label} needs your attention. Requested by host {request.user.get_full_name() or request.user.username}.'
                )
                messages.success(request, f'Notification sent to {table.assigned_server.get_full_name()}.')
            else:
                messages.warning(request, f'Table {table.label} has no orders yet. Assign a server first so they can be notified.')
        else:
            messages.warning(request, 'No server assigned to this table.')

        return redirect('server_table_detail', table_id=table_id)

    return redirect('server_host_view')