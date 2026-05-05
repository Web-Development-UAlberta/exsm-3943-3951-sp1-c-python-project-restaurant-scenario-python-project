from django.shortcuts import render, get_object_or_404, redirect
from .models import Restaurant, User, Tag
from.forms import RestaurantForm, TagForm

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

def restaurant_confirm_delete(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        restaurant.delete()
        return redirect('restaurant_list')
    return render(request, 'restaurant/restaurant_confirm_delete.html', {'restaurant': restaurant})

def restaurant_toggle_active(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.user.role == User.Role.MANAGER:
        restaurant.is_active = not restaurant.is_active
        restaurant.save()
    return redirect('restaurant_detail', pk=pk)

#=======Tag=======

def tag_list(request):
    tags = Tag.objects.all()
    return render(request, 'restaurant/tag_list.html', {'tags': tags})

def tag_detail(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    return render(request, 'restaurant/tag_detail.html', {'tag':tag })

def tag_create(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save() 
            return redirect('tag_list')
    else:
        form = TagForm()
    return render(request, 'restaurant/tag_form.html', {'form': form})

def tag_edit(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            return redirect ('tag_list')
    else:
        form = TagForm(instance=tag)
    return render(request, 'restaurant/tag_form.html', {'form': form})