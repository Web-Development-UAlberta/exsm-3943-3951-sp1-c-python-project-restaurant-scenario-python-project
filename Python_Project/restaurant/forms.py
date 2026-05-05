from django import forms
from .models import Restaurant, Category

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'address', 'phone_number', 'opening_time', 'closing_time',
                  'latitude', 'longitude']
        

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']