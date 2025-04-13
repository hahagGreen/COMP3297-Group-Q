from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from .models import Accommodation, Reservation
from .serializers import AccommodationSerializer, ReservationSerializer
import json
import requests
# Create your views here.

def fetch_coordinates(location):
    url = "https://www.als.gov.hk/lookup?"
    params = {
        "q": location.upper(),
        "n": 1,
    }
    try:
        res = requests.get(url=url, params=params,headers={"Accept": "application/json"})
        res.raise_for_status()  # Raise an error for bad responses
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coordinates: {e}")
        return None
    return res, res.status_code

# Retrieve geolocation data from the API json response
def getGeoAddress(jsonData):
    print(jsonData)
    data = jsonData["SuggestedAddress"][0]["Address"]["PremisesAddress"]
    geogAddr = data.get("GeoAddress")
    latitude = data.get("GeospatialInformation").get("Latitude")
    longitude = data.get("GeospatialInformation").get("Longitude")
    return geogAddr, latitude, longitude

def setAccommodation(data):
    accommodation = Accommodation()
    accommodation.availability_start = data.get("startDate")
    accommodation.availability_end = data.get("endDate")
    accommodation.type = data.get("type")
    accommodation.beds = data.get("beds")   
    accommodation.bedrooms = data.get("bedrooms")
    accommodation.price = data.get("price")
    accommodation.address = data.get("address")
    query = fetch_coordinates(accommodation.address)[0]
    accommodation.geo_address, accommodation.latitude, accommodation.longitude = getGeoAddress(json.loads(query.text))
    return accommodation
    
def add_accommodations(request):
    if request.method == "POST":
        # Handle form submission here
        # For example, save the accommodation details to the database
        accommodation = setAccommodation(request.POST)
        accommodation.save()
        # Save the accommodation instance to the database
        return render(request, "add.html", {"messages": "Accommodation added successfully!", "accommodation": accommodation})
    return render(request, "add.html")

def api_add(request):
    if request.method == "POST":
        accommodation = setAccommodation(request.POST)
        accommodation.save()
        accommodation_details = {
            'id': accommodation.accommodation_id,
            'startDate': accommodation.availability_start,
            'endDate': accommodation.availability_end,
            'type': accommodation.type,
            'numOfBeds': accommodation.beds,
            'numOfBedrooms': accommodation.bedrooms,
            'price': accommodation.price,
            'address': accommodation.address,
            'geo_address': accommodation.geo_address,
            'latitude': accommodation.latitude,
            'longitude': accommodation.longitude,
        }
        return JsonResponse(accommodation_details)
    else:
        return HttpResponse("Invalid request method.")

def api_cancel_reservation(request):
    """Epic 4.1 Cancel Reservation."""
    if request.method == 'POST' or request.method == 'GET':
        reservation_id = request.POST.get("reservation_id") if request.method == 'POST' else request.GET.get("reservation_id")
        if reservation_id:
            try:
                # Update reservation status to 'canceled'
                updated_count = Reservation.objects.filter(
                    reservation_id=reservation_id
                ).update(status="canceled")
                
                if updated_count:
                    # Get the accommodation_id from the reservation
                    reservation = Reservation.objects.get(reservation_id=reservation_id)
                    accommodation_id = reservation.accommodation_id
                    
                    # Modify is_reserved in table Accommodation from 1 to 0.
                    Accommodation.objects.filter(
                        accommodation_id=accommodation_id
                    ).update(is_reserved=0)
                    return JsonResponse({'message': 'Reservation Canceled'})
                else:
                    return JsonResponse({'error': 'No matching reservation found'}, status=404)
            except Exception as e:
                print(f"Error cancelling reservation: {e}")
                return JsonResponse({'error': 'Error cancelling reservation'}, status=500)
        else:
            return JsonResponse({'error': 'Reservation ID not provided'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def api_view_active_reservations(request):
    """Epic 4.2 View Active Reservations."""
    if request.method == 'GET':
        # Fetch active reservations
        active_reservations = Reservation.objects.filter(status__in=['pending', 'confirmed'])
        serializer = ReservationSerializer(active_reservations, many=True)
        return JsonResponse({'reservations': serializer.data})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

