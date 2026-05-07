from django.shortcuts import render, get_object_or_404, redirect
from restaurant import models
from django.contrib.auth import login as auth_login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from restaurant import forms
from django.urls import reverse
from django.db.models import Q




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




# ====================== EXISTING VIEWS ======================


def restaurant_list(request):
    restaurants = models.Restaurant.objects.all()
    return render(request, 'restaurant/restaurant_list.html', {'restaurants': restaurants})


def restaurant_detail(request, pk):
    restaurant = get_object_or_404(models.Restaurant, pk=pk)
    return render(request, 'restaurant/restaurant_detail.html', {'restaurant': restaurant})


def restaurant_create(request):
    if request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('restaurant_list')
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


def restaurant_edit(request, pk):
    if request.user.role != models.User.Role.MANAGER and request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('restaurant_list')
    restaurant = get_object_or_404(models.Restaurant, pk=pk)
    if request.method == 'POST':
        form = forms.RestaurantForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            return redirect('restaurant_list')
    else:
        form = forms.RestaurantForm(instance=restaurant)
    return render(request, 'restaurant/restaurant_create.html', {'form': form})


def restaurant_confirm_delete(request, pk):
    if request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('restaurant_list')
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


def restaurant_toggle_active(request, pk):
    restaurant = get_object_or_404(models.Restaurant, pk=pk)
    if request.user.role == models.User.Role.MANAGER or request.user.role == models.User.Role.OWNER:
        restaurant.is_active = not restaurant.is_active
        restaurant.save()
    return redirect('restaurant_detail', pk=pk)




# ====================== BASIC VIEWS ======================


def customer_index(request):
    return render(request, 'restaurant/customer_index.html')


def user_logout(request):
    logout(request)
    return redirect('index')


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


@login_required
def manager_view(request):
    if request.user.role != models.User.Role.MANAGER and request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('staff_index')
    return render(request, 'restaurant/manager_view.html')


@login_required
@user_passes_test(is_server_or_manager)
def server_host_view(request):
    """Server/Host Dashboard"""
    tables = models.Table.objects.all().order_by('label')
    context = {'tables': tables}
    return render(request, 'restaurant/server_host_view.html', context)


@login_required
@user_passes_test(is_kitchen_or_manager)
def kitchen_view(request):
    """Kitchen Dashboard"""
    orders = models.Order.objects.filter(
        order_status__in=[models.Order.OrderStatus.PENDING, models.Order.OrderStatus.PREPARING]
    ).order_by('created_at')
    context = {'orders': orders}
    return render(request, 'restaurant/kitchen_view.html', context)


@login_required
def driver_view(request):
    return render(request, 'restaurant/driver_view.html')


@login_required
def owner_view(request):
    return render(request, 'restaurant/owner_view.html')




# ====================== STAFF BUSINESS LOGIC ======================


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
        server = get_object_or_404(models.User, id=server_id, role=models.User.Role.SERVER_HOST)
       
        messages.success(request, f"Server {server.get_full_name() or server.username} assigned to Table {table.label}")
        return redirect('server_host_view')
   
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
        order.save()
        messages.success(request, f'Order #{order.id} status updated to {order.get_order_status_display()}')
        return redirect('kitchen_view')
   
    context = {
        'order': order,
        'status_choices': models.Order.OrderStatus.choices,
    }
    return render(request, 'restaurant/update_order_status.html', context)

