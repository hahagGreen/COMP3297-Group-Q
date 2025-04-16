# accommodations/forms.py
from django import forms
from .models import Campus

class AccommodationSearchForm(forms.Form):
    accommodation_type = forms.CharField(required=False, label='Accommodation Type')
    availability_start = forms.DateField(required=False, label='Availability Start', input_formats=['%Y-%m-%d'])
    availability_end = forms.DateField(required=False, label='Availability End', input_formats=['%Y-%m-%d'])
    min_beds = forms.IntegerField(required=False, min_value=1, label='Minimum Beds', initial=1)
    min_bedrooms = forms.IntegerField(required=False, min_value=1, label='Minimum Bedrooms', initial=1)
    max_price = forms.FloatField(required=False, min_value=0, label='Maximum Price')
    campus = forms.ModelChoiceField(queryset=Campus.objects.all(), required=False, label='Sort by Distance from Campus')
    is_reserved = forms.BooleanField(required=False, label='Show Reserved', initial=0)