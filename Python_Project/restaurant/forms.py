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


class CustomerEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput,
        required=False  # not required so customer can update other fields without changing password
    )
    password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput,
        required=False
    )

    class Meta:
        model = models.Customer
        fields = ['phone_number', 'address']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # only validate passwords if the customer is trying to change them
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError('Passwords do not match.')
        return cleaned_data


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

class TableForm(forms.ModelForm):
    class Meta:
        model = models.Table
        fields = ['label', 'seats']
        
class TagForm(forms.ModelForm):
    class Meta:
        model = models.Tag
        fields = ['name']
        
class MenuItemForm(forms.ModelForm):
    class Meta:
        model = models.MenuItem
        fields = ['category', 'name', 'description', 'price', 'image']


class OrderForm(forms.ModelForm):
    POINTS_CHOICES = [
        (False, 'Do not use loyalty points'),
        (True, 'Use loyalty points for a discount'),
    ]

    redeem_points = forms.ChoiceField(
        choices=POINTS_CHOICES,
        widget=forms.Select,
        required=False,
        label='Loyalty Points'
    )

    class Meta:
        model = models.Order
        fields = ['order_type', 'delivery_address', 'special_instruction']
        widgets = {
            'delivery_address': forms.TextInput(attrs={'placeholder' : 'Required for delivery orders only'}),
            'special_instruction' : forms.Textarea(attrs={'rows' : 3, 'placeholder' : 'Any special requests or dietary notes'}),
        }

    # redefining the inbuild clean() method
    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('order_type')
        delivery_address = cleaned_data.get('delivery_address')

        # delivery address is required if order type is delivery
        if order_type == models.Order.OrderType.DELIVERY and not delivery_address:
            raise forms.ValidationError('Delivery address is required for delivery orders.')

        return cleaned_data
    


class ReservationForm(forms.ModelForm):
    class Meta:
        model = models.Reservation
        fields = ['restaurant', 'table', 'reservation_datetime', 'party_size',
                  'guest_name', 'guest_email', 'guest_phone_number']
        widgets = {
            'reservation_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'guest_name': forms.TextInput(attrs={'placeholder': 'Required if not logged in'}),
            'guest_email': forms.EmailInput(attrs={'placeholder': 'Required if not logged in'}),
            'guest_phone_number': forms.TextInput(attrs={'placeholder': 'Required if not logged in'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        reservation_datetime = cleaned_data.get('reservation_datetime')
        party_size = cleaned_data.get('party_size')
        table = cleaned_data.get('table')

        from django.utils import timezone
        if reservation_datetime and reservation_datetime < timezone.now():
            raise forms.ValidationError('Reservation time cannot be in the past.')

        if party_size and party_size > 20:
            raise forms.ValidationError('Maximum party size is 20. For larger groups please contact us directly.')

        if table and party_size and table.seats < party_size:
            raise forms.ValidationError(f'This table only seats {table.seats} people.')

        return cleaned_data


class InventoryForm(forms.ModelForm):
    class Meta:
        model = models.Inventory
        fields = ['ingredient_name', 'current_level', 'unit', 'reorder_level']