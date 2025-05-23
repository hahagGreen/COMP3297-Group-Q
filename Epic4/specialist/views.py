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
    """Epic 4.1 Cancel reservation via POST with URL parameter."""
    if request.method == 'POST':
        reservation_id = request.GET.get("reservation_id")  # Get from URL query
        if not reservation_id:
            return JsonResponse({'error': 'Reservation ID not provided'}, status=400)
        
        try:
            reservation = Reservation.objects.get(reservation_id=reservation_id)
            reservation.status = Reservation.CANCELED
            reservation.save()  # Triggers save() to update Accommodation.is_reserved
            return JsonResponse({'message': 'Reservation canceled successfully'})
        
        except Reservation.DoesNotExist:
            return JsonResponse({'error': 'Reservation not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
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
    
def api_modify(request):
    """Epic 4.3 Modify reservation status via POST with URL parameters."""
    if request.method == 'POST':
        reservation_id = request.GET.get('reservation_id')  # From URL parameters
        new_status = request.GET.get('status')             # From URL parameters

        if not reservation_id or not new_status:
            return JsonResponse({'error': 'Missing reservation_id or status'}, status=400)

        try:
            reservation = Reservation.objects.get(reservation_id=reservation_id)
            valid_statuses = [status[0] for status in Reservation.STATUS_CHOICES]
            
            if new_status not in valid_statuses:
                return JsonResponse({'error': 'Invalid status'}, status=400)
            
            # Update reservation status
            reservation.status = new_status
            reservation.save()  # Triggers save() to update Accommodation.is_reserved
            
            return JsonResponse({'message': f'Reservation {reservation_id} status updated to {new_status}'})
        
        except Reservation.DoesNotExist:
            return JsonResponse({'error': 'Reservation not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
