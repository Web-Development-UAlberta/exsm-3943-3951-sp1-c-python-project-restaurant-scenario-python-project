from django.shortcuts import render, get_object_or_404, redirect
from .models import Restaurant
from.forms import RestaurantForm

def restaurant_list(request):
    restaurants = Restaurant.objects.all()
    return render(request, 'restaurant/restaurant_list.html', {'restaurants': restaurants})
        
def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    return render(request, 'restaurant/restaurant_detail.html', {'restaurant':restaurant })

def restaurant_create(request):
    if request.method == 'POST':
        form = RestaurantForm(request.POST)
        if form.is_valid():
            restaurant = form.save(commit=False) # builds object but doesn't save yet
            restaurant.user = request.user # assign the logged in user
            restaurant.save() # will write to database now with the update
            return redirect('restaurant_list')
    else:
        form = RestaurantForm()
    return render(request, 'restaurant/restaurant_form.html', {'form': form})

def restaurant_edit(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        form = RestaurantForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            return redirect ('restaurant_list')
    else:
        form = RestaurantForm(instance=restaurant)
    return render(request, 'restaurant/restaurant_form.html', {'form': form})

def restaurant_delete(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        restaurant.delete()
        return redirect('restaurant_list')
    return render(request, 'restaurant/restaurant_confirm_delete.html', {'restaurant': restaurant})

        

