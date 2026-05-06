from django.shortcuts import render, get_object_or_404, redirect
from restaurant import models
from django.contrib.auth import login as auth_login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from restaurant import forms
from django.urls import reverse


def restaurant_list(request):
    restaurants = models.Restaurant.objects.all()
    return render(request, 'restaurant/restaurant_list.html', {'restaurants': restaurants})
        
def restaurant_detail(request, pk):
    restaurant = get_object_or_404(models.Restaurant, pk=pk)
    return render(request, 'restaurant/restaurant_detail.html', {'restaurant':restaurant })


def restaurant_create(request):
    if request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('restaurant_list')
    if request.method == 'POST':
        form = forms.RestaurantForm(request.POST)
        if form.is_valid():
            restaurant = form.save(commit=False) # builds object but doesn't save yet
            restaurant.user = request.user # assign the logged in user
            restaurant.save() # will write to database now with the update
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
            return redirect ('restaurant_list')
    else:
        form = forms.RestaurantForm(instance=restaurant)
    return render(request, 'restaurant/restaurant_create.html', {'form': form})

def confirm_delete(request, pk):
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



# View to display the homepage of the web-app for customers
def customer_index(request):
    return render(request, 'restaurant/customer_index.html')

# Logic to Logout a user
def user_logout(request):
    logout(request)
    return redirect('index')

# View to login the customers
def customer_login(request):
    if 'next' in request.GET: # this will make sure that any request that is coming via 'redirect' shows appropriate message
        messages.warning(request, 'You need to Login first to access this page!')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username = username, password = password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Login Successful!')
            return redirect('index')
        
        else:
            messages.error(request, 'Invalid username or password!')

    return render(request, 'restaurant/customer_login.html')

# View to sing-up a customer
def customer_signup(request):

    if request.method == 'POST':
        form = forms.CustomerSignUpForm(request.POST) 

        if form.is_valid():
            user = form.save(commit=False) # this will not save the info to the db yet, just create an object
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.role = 5 # default value for 'customer'
            user.save()# this save will create information in the user table and not in my customer table
            
            # Making an object for our 'Customer' table to store all the data
            models.Customer.objects.create(
                user = user,
                phone_number = form.cleaned_data['phone_number'],
                address= form.cleaned_data['address']
            )

            return redirect('customer_login')

    else:
        form = forms.CustomerSignUpForm()

    return render(request, 'restaurant/customer_signup.html', {'form':form})

# View to display the homepage of the web-app for customers
@login_required
def staff_index(request):
    return render(request, 'restaurant/staff_index.html')

# View to login staff members
def staff_login(request):
    if 'next' in request.GET: # this will make sure that any request that is coming via 'redirect' shows appropriate message
        messages.warning(request, 'You need to Login first to access this page!')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.role == models.User.Role.CUSTOMER:
                messages.error(request, 'Invalid username or password!')
            else:
                auth_login(request, user)
                messages.success(request, 'Login Successful!')
                
                # redirecting the staff member based on role
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


# View to sign-up a staff member
def staff_signup(request):

    if request.method == 'POST':
        form = forms.StaffSignUpForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']

            # check if the email has been pre-approved by admin in StaffInvite table
            invite = models.StaffInvite.objects.filter(email=email, is_used=False).first()

            if not invite:
                messages.error(request, 'This email has not been approved for staff registration.')
            else:
                user = form.save(commit=False) # this will not save the info to the db yet, just create an object
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.role = invite.role # assign role from the invite record
                user.save() # this save will create information in the user table

                # mark the invite as used so it cannot be reused
                invite.is_used = True
                invite.save()

                return redirect('staff_login')

    else:
        form = forms.StaffSignUpForm()

    return render(request, 'restaurant/staff_signup.html', {'form': form})


# View for the Manager (role 1)
@login_required
def manager_view(request):
    if request.user.role != models.User.Role.MANAGER and request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('staff_index')
    
    return render(request, 'restaurant/manager_view.html')

# View for the Server/Host (role 2)
@login_required
def server_host_view(request):
    if request.user.role != models.User.Role.SERVER_HOST and request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('staff_index')
    
    return render(request, 'restaurant/server_host_view.html')

# View for the Kitchen Staff (role 3)
@login_required
def kitchen_view(request):
    if request.user.role != models.User.Role.KITCHEN_STAFF and request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('staff_index')
    
    return render(request, 'restaurant/kitchen_view.html')

# View for Delivery driver (role 4)
@login_required
def driver_view(request):
    if request.user.role != models.User.Role.DELIVERY_DRIVER and request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('staff_index')
    
    return render(request, 'restaurant/driver_view.html')


# View for Owner (role 6)
@login_required
def owner_view(request):
    if request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('staff_index')
    
    return render(request, 'restaurant/owner_view.html')
    

# View to add staff from admin panel
#@login_required
#def add_staff(request):


# View to place an order
#@login_required
# def order_create(request)

# View to book a table
# def book_table(request)


#===========Categories==========#
def category_list(request):
    categories = models.Category.objects.all()
    return render(request, 'restaurant/category_list.html', {'categories': categories})

def category_detail(request, pk):
    category = get_object_or_404(models.Category, pk=pk)
    return render(request, 'restaurant/category_detail.html', {'category':category})

@login_required
def category_create(request):
    if request.user.role != models.User.Role.MANAGER and request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('category_list')
    if request.method == 'POST':
        form = forms.CategoryForm(request.POST)
        if form.is_valid():
            form.save() 
            return redirect('category_list')
    else:
        form = forms.CategoryForm()
    return render(request, 'restaurant/category_form.html', {'form': form})

@login_required
def category_edit(request, pk):
    if request.user.role != models.User.Role.MANAGER and request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('category_list')
    category = get_object_or_404(models.Category, pk=pk)
    if request.method == 'POST':
        form = forms.CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect ('category_list')
    else:
        form = forms.CategoryForm(instance=category)
    return render(request, 'restaurant/category_form.html', {'form': form})

@login_required
def category_confirm_delete(request, pk):
    if request.user.role != models.User.Role.MANAGER and request.user.role != models.User.Role.OWNER:
        messages.error(request, 'Unauthorized User, Access Denied!')
        return redirect('category_list')
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