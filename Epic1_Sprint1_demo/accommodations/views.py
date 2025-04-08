# accommodations/views.py
from django.shortcuts import render
from .forms import AccommodationSearchForm
from .models import Accommodation, Campus
import requests
import xml.etree.ElementTree as ET
import math
from django.http import JsonResponse


def search_accommodations_api(request):
    # Initialize the form with GET parameters
    form = AccommodationSearchForm(request.GET)
    print(f"Request GET: {request.GET}")
    print(f"Form is bound: {form.is_bound}")
    print(f"Form is valid: {form.is_valid()}")
    print(f"Form errors: {form.errors}")
    
    # Check if the form is valid
    if form.is_valid():
        # Start with all accommodations
        query = Accommodation.objects.all()

        if form.cleaned_data['is_reserved']:
            query = query.filter(is_reserved=form.cleaned_data['is_reserved'])
        else:
            query = query.exclude(is_reserved=True)  # Exclude reserved accommodations

        # Apply filters based on form data
        if form.cleaned_data['accommodation_type']:
            query = query.filter(type=form.cleaned_data['accommodation_type'])
        if form.cleaned_data['availability_start'] and form.cleaned_data['availability_end']:
            query = query.filter(
                availability_start__lte=form.cleaned_data['availability_end'],
                availability_end__gte=form.cleaned_data['availability_start']
            )
        if form.cleaned_data['min_beds']:
            query = query.filter(beds__gte=form.cleaned_data['min_beds'])
        if form.cleaned_data['min_bedrooms']:
            query = query.filter(bedrooms__gte=form.cleaned_data['min_bedrooms'])
        if form.cleaned_data['max_price']:
            query = query.filter(price__lte=form.cleaned_data['max_price'])
        
        # Convert queryset to list for further processing
        accommodations = list(query)
        
        # Initialize list for active filters
        active_filters = []
        
        # Collect active filters
        if form.cleaned_data['accommodation_type']:
            active_filters.append(f"Type: {form.cleaned_data['accommodation_type']}")
        if form.cleaned_data['availability_start'] and form.cleaned_data['availability_end']:
            active_filters.append(
                f"Availability: {form.cleaned_data['availability_start'].strftime('%Y-%m-%d')} to "
                f"{form.cleaned_data['availability_end'].strftime('%Y-%m-%d')}"
            )
        if form.cleaned_data['min_beds']:
            active_filters.append(f"Minimum Beds: {form.cleaned_data['min_beds']}")
        if form.cleaned_data['min_bedrooms']:
            active_filters.append(f"Minimum Bedrooms: {form.cleaned_data['min_bedrooms']}")
        if form.cleaned_data['max_price']:
            active_filters.append(f"Max Price: {form.cleaned_data['max_price']:.2f}")
        
        # Handle campus-based distance sorting
        if form.cleaned_data['campus']:
            campus = form.cleaned_data['campus']
            campus_lat, campus_lon = campus.latitude, campus.longitude
            for acc in accommodations:
                # Geocode if coordinates are missing
                if not acc.latitude or not acc.longitude:
                    acc.latitude, acc.longitude = get_geocode_by_address(acc.address)
                    if acc.latitude and acc.longitude:
                        acc.save()
                # Calculate distance
                if acc.latitude and acc.longitude:
                    acc.distance = calc_distance(acc.latitude, acc.longitude, campus_lat, campus_lon)
                else:
                    acc.distance = float('inf')
            # Sort by distance
            accommodations.sort(key=lambda x: x.distance)
            active_filters.append(f"Sorted by distance from: {campus.name}")
        
        # Prepare accommodation data for JSON
        accommodations_data = []
        for acc in accommodations:
            acc_data = {
                'id': acc.accommodation_id,
                'type': acc.type,
                'availability_start': acc.availability_start.isoformat(),
                'availability_end': acc.availability_end.isoformat(),
                'beds': acc.beds,
                'bedrooms': acc.bedrooms,
                'price': float(acc.price),  # Convert Decimal to float for JSON
                'address': acc.address,
                'latitude': acc.latitude,
                'longitude': acc.longitude,
                'geo_address': acc.geo_address,
                'is_reserved': acc.is_reserved
            }
            # Include distance if calculated
            if hasattr(acc, 'distance'):
                acc_data['distance'] = acc.distance if acc.distance != float('inf') else None
            accommodations_data.append(acc_data)
        
        # Return JSON response
        return JsonResponse({
            'filters': active_filters,
            'accommodations': accommodations_data
        })
    else:
        # Return errors if form is invalid
        return JsonResponse({'errors': form.errors}, status=400)


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