# accommodations/views.py
import datetime
from django.shortcuts import render
from .forms import AccommodationSearchForm
from .models import Accommodation, Campus, Specialist
from .serializers import AccommodationSerializer
import requests
import xml.etree.ElementTree as ET
import math
from rest_framework.response import Response
from datetime import datetime
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404

class Search_Accommodations_API(APIView):
    def get(self, request):
        params = request.GET
        errors = {}
        accommodation_type = params.get('accommodation_type')
        
        # Parse and validate availability dates
        availability_start = params.get('availability_start')
        availability_end = params.get('availability_end')
        start_date = end_date = None
        if availability_start:
            try:
                start_date = datetime.strptime(availability_start, '%Y-%m-%d').date()
            except ValueError:
                errors['availability_start'] = ['Invalid date format. Use YYYY-MM-DD.']
        if availability_end:
            try:
                end_date = datetime.strptime(availability_end, '%Y-%m-%d').date()
            except ValueError:
                errors['availability_end'] = ['Invalid date format. Use YYYY-MM-DD.']
        if start_date and end_date and start_date > end_date:
            errors['availability'] = ['Start date must be before end date.']
        
        # Validate min_beds
        min_beds = params.get('min_beds')
        if min_beds is not None:
            try:
                min_beds = int(min_beds)
                if min_beds < 1:
                    errors['min_beds'] = ['Ensure this value is greater than or equal to 1.']
            except ValueError:
                errors['min_beds'] = ['A valid integer is required.']
        
        # Validate min_bedrooms
        min_bedrooms = params.get('min_bedrooms')
        if min_bedrooms is not None:
            try:
                min_bedrooms = int(min_bedrooms)
                if min_bedrooms < 1:
                    errors['min_bedrooms'] = ['Ensure this value is greater than or equal to 1.']
            except ValueError:
                errors['min_bedrooms'] = ['A valid integer is required.']
        
        # Validate max_price
        max_price = params.get('max_price')
        if max_price is not None:
            try:
                max_price = float(max_price)
                if max_price < 0:
                    errors['max_price'] = ['Ensure this value is greater than or equal to 0.']
            except ValueError:
                errors['max_price'] = ['A valid number is required.']
        
        # Validate campus
        campus_id = params.get('campus')
        campus = None
        if campus_id is not None:
            try:
                campus = Campus.objects.get(campus_id=int(campus_id))
            except (ValueError, Campus.DoesNotExist):
                errors['campus'] = ['Invalid campus ID.']
        
        # Validate is_reserved
        is_reserved = params.get('is_reserved')
        is_reserved_bool = None
        if is_reserved is not None:
            lower_val = is_reserved.lower()
            if lower_val in ('true', '1'):
                is_reserved_bool = True
            elif lower_val in ('false', '0'):
                is_reserved_bool = False
            else:
                errors['is_reserved'] = ['A valid boolean value is required (e.g., true, 1, false, 0).']
        
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        # Apply filters
        queryset = Accommodation.objects.all()
        
        if accommodation_type:
            queryset = queryset.filter(type=accommodation_type)
        if start_date:
            queryset = queryset.filter(availability_start__lte=start_date)
        if end_date:
            queryset = queryset.filter(availability_end__gte=end_date)
        if min_beds is not None:
            queryset = queryset.filter(beds__gte=min_beds)
        if min_bedrooms is not None:
            queryset = queryset.filter(bedrooms__gte=min_bedrooms)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        if is_reserved_bool is not None:
            queryset = queryset.filter(is_reserved=is_reserved_bool)
        
        # Process accommodations: geocode if needed
        accommodations = list(queryset)
        for acc in accommodations:
            if acc.latitude is None or acc.longitude is None:
                lat, lon = get_geocode_by_address(acc.address)
                if lat is not None and lon is not None:
                    acc.latitude = lat
                    acc.longitude = lon
                    acc.geo_address = acc.address  # Assuming geo_address is the same as address
                    acc.save()
        
        # Calculate distances and sort if campus is provided
        campus_name = None
        if campus:
            campus_lat = campus.latitude
            campus_lon = campus.longitude
            campus_name = campus.name
            for acc in accommodations:
                distance = calc_distance(acc.latitude, acc.longitude, campus_lat, campus_lon)
                acc.distance = distance
            accommodations.sort(key=lambda x: x.distance)
        else:
            for acc in accommodations:
                acc.distance = None
        
        # Build filters list
        filters = []
        if accommodation_type:
            filters.append(f"Type: {accommodation_type}")
        if start_date and end_date:
            filters.append(f"Available from {start_date} to {end_date}")
        elif start_date:
            filters.append(f"Available from {start_date}")
        elif end_date:
            filters.append(f"Available until {end_date}")
        if min_beds is not None:
            filters.append(f"Minimum Beds: {min_beds}")
        if min_bedrooms is not None:
            filters.append(f"Minimum Bedrooms: {min_bedrooms}")
        if max_price is not None:
            filters.append(f"Maximum Price: HKD {max_price:.2f}")
        if is_reserved_bool is not None:
            status_str = "Reserved accommodations only" if is_reserved_bool else "Available for reservation only"
            filters.append(status_str)
        if campus:
            filters.append(f"Sorted by distance from: {campus_name}")
        
        # Serialize data
        serializer = AccommodationSerializer(accommodations, many=True)
        response_data = {
            'filters': filters,
            'accommodations': serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

        


    
# 保持其他函数（get_geocode_by_address, calc_distance, search_accommodations）不变
def search_accommodations(request):
    form = AccommodationSearchForm(request.GET or None)
    accommodations = []
    campuses = Campus.objects.all()
    active_filters = []  # Initialize active filters list

    if request.method == 'GET' and form.is_valid():
        # Start with all accommodations
        query = Accommodation.objects.all()

        # Apply filters based on form input
        if form.cleaned_data['accommodation_type']:
            query = query.filter(type=form.cleaned_data['accommodation_type'])

        if form.cleaned_data['availability_start'] and form.cleaned_data['availability_end']:
            query = query.filter(
                availability_start__lte=form.cleaned_data['availability_end'].isoformat(),
                availability_end__gte=form.cleaned_data['availability_start'].isoformat()
            )

        if form.cleaned_data['min_beds']:
            query = query.filter(beds__gte=form.cleaned_data['min_beds'])

        if form.cleaned_data['min_bedrooms']:
            query = query.filter(bedrooms__gte=form.cleaned_data['min_bedrooms'])

        if form.cleaned_data['max_price']:
            query = query.filter(price__lte=form.cleaned_data['max_price'])

        accommodations = list(query)

        # Sort by distance if a campus is selected
        if form.cleaned_data['campus']:
            campus = form.cleaned_data['campus']
            campus_lat, campus_lon = campus.latitude, campus.longitude

            for acc in accommodations:
                # Geocode address if coordinates are missing
                if not acc.latitude or not acc.longitude:
                    acc.latitude, acc.longitude = get_geocode_by_address(acc.address)
                    acc.save()  # Save coordinates to the database

                # Calculate distance
                acc.distance = calc_distance(acc.latitude, acc.longitude, campus_lat, campus_lon)

            # Sort accommodations by distance
            accommodations.sort(key=lambda x: x.distance)
        # Collect applied filters
        accommodation_type = form.cleaned_data.get('accommodation_type')
        if accommodation_type:
            active_filters.append(f"Type: {accommodation_type}")

        availability_start = form.cleaned_data.get('availability_start')
        availability_end = form.cleaned_data.get('availability_end')
        if availability_start and availability_end:
            active_filters.append(
                f"Availability: {availability_start.strftime('%Y-%m-%d')} to "
                f"{availability_end.strftime('%Y-%m-%d')}"
            )

        min_beds = form.cleaned_data.get('min_beds')
        if min_beds:
            active_filters.append(f"Minimum Beds: {min_beds}")

        min_bedrooms = form.cleaned_data.get('min_bedrooms')
        if min_bedrooms:
            active_filters.append(f"Minimum Bedrooms: {min_bedrooms}")

        max_price = form.cleaned_data.get('max_price')
        if max_price:
            active_filters.append(f"Max Price: HKD {max_price:.2f}")

        campus = form.cleaned_data.get('campus')
        if campus:
            active_filters.append(f"Sorted by distance from: {campus.name}")

    return render(request, 'accommodations/search.html', {
        'form': form,
        'accommodations': accommodations,
        'campuses': campuses,
        'active_filters': active_filters  # Add to context
    })

def get_geocode_by_address(address):
    """Fetch latitude and longitude from DATA.GOV.HK API."""
    try:
        response = requests.get("https://www.als.gov.hk/lookup", params={"q": address}, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        lat = float(root.find(".//Latitude").text)
        lon = float(root.find(".//Longitude").text)
        return lat, lon
    except Exception as e:
        print(f"Geocoding failed for '{address}': {e}")
        return None, None

def calc_distance(lat1, lon1, lat2, lon2):
    """Calculate distance using equirectangular approximation."""
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    x = (lon2 - lon1) * math.cos((lat1 + lat2) / 2)
    y = lat2 - lat1
    return math.sqrt(x**2 + y**2) * 6371  # Earth radius in km