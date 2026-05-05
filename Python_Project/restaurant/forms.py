from django import forms
from .models import Restaurant, Tag

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'address', 'phone_number', 'opening_time', 'closing_time',
                  'latitude', 'longitude']
        








class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']