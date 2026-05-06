from django import forms
from restaurant import models
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model() # this will return me the 'user' model that we have configured in our database

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = models.Restaurant
        fields = ['name', 'address', 'phone_number', 'opening_time', 'closing_time',
                  'latitude', 'longitude']
        

class CustomerSignUpForm(UserCreationForm):
    phone_number = forms.CharField(max_length=10)
    address = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2', 'phone_number', 'address']
        # ^ Using the inbuilt fields from AbstractUser class along with my manually set up fields


class StaffSignUpForm(UserCreationForm):
    phone_number = forms.CharField(max_length=10)
    address = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2', 'phone_number', 'address']
        # ^ Using the inbuilt fields from AbstractUser class along with my manually set up fields

class AddStaffForm(forms.ModelForm):
    class Meta:
        model = models.StaffInvite
        fields = ['email', 'role']
        
class CategoryForm(forms.ModelForm):
    class Meta:
        model = models.Category
        fields = ['name']

class TagForm(forms.ModelForm):
    class Meta:
        model = models.Tag
        fields = ['name']