from django.shortcuts import render, HttpResponse, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from .models import Accommodation, User, Reservation
import json
import requests
from .serializers import AccommodationSerializer, ReservationSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

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
    data = jsonData["SuggestedAddress"][0]["Address"]["PremisesAddress"]
    geogAddr = data.get("GeoAddress")
    latitude = data.get("GeospatialInformation").get("Latitude")
    longitude = data.get("GeospatialInformation").get("Longitude")
    return geogAddr, latitude, longitude

def setAccommodation(data, isUpdated=False, accommodation=None):
    if not isUpdated:
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

def checkExistence(accommodation_id):
    try:
        accommodation = Accommodation.objects.get(accommodation_id=accommodation_id)
        return True
    except Accommodation.DoesNotExist:
        return False

# api for specialist adding accommodation details 
@extend_schema(
    summary="Add new accommodation",
    description="Add a new accommodation to the system. Only accessible by specialists.",
    parameters=[
        OpenApiParameter(name="userId", type=int, required=True),
        OpenApiParameter(name="startDate", type=str, required=True),
        OpenApiParameter(name="endDate", type=str, required=True),
        OpenApiParameter(name="type", type=str, required=True),
        OpenApiParameter(name="beds", type=int, required=True),
        OpenApiParameter(name="bedrooms", type=int, required=True),
        OpenApiParameter(name="price", type=float, required=True),
        OpenApiParameter(name="address", type=str, required=True),
    ],
    responses={
        201: AccommodationSerializer,
        403: OpenApiResponse(description='User is not a specialist'),
        404: OpenApiResponse(description='User not found'),
    }
)
@api_view(['POST'])
def api_add(request):
    userId = request.POST.get('userId')
    try :
        user = User.objects.get(user_id=userId)
        if(user.role != 'Specialist'):
            return JsonResponse({'error': 'You cannot access to this'}, status=403)
        # Testing the user role
        # else :
        #     print(user.name)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    accommodation = setAccommodation(request.POST)
    accommodation.save()
    serializers = AccommodationSerializer(accommodation)
    return Response(serializers.data)

# api for specialist editing accommodation details
@extend_schema(
    summary="Edit accommodation",
    description="Edit an existing accommodation's details. Only accessible by specialists.",
    parameters=[
        OpenApiParameter(name="userId", type=int, required=True),
        OpenApiParameter(name="accId", type=int, required=True),
        OpenApiParameter(name="startDate", type=str, required=True),
        OpenApiParameter(name="endDate", type=str, required=True),
        OpenApiParameter(name="type", type=str, required=True),
        OpenApiParameter(name="beds", type=int, required=True),
        OpenApiParameter(name="bedrooms", type=int, required=True),
        OpenApiParameter(name="price", type=float, required=True),
        OpenApiParameter(name="address", type=str, required=True),
    ],
    responses={
        200: AccommodationSerializer,
        403: OpenApiResponse(description='User is not a specialist'),
        404: OpenApiResponse(description='User or Accommodation not found'),
    }
)
@api_view(['POST'])
def api_edit(request):
    userId = request.POST.get('userId')
    try :
        user = User.objects.get(user_id=userId)
        if(user.role != 'Specialist'):
            return JsonResponse({'error': 'You cannot access to this as you are not a specialist'}, status=403)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    accommodation_id = request.POST.get('accId')
    if not checkExistence(accommodation_id):
        return JsonResponse({'error': 'Accommodation not found'}, status=404)
    accommodation = Accommodation.objects.get(accommodation_id=accommodation_id)
    accommodation = setAccommodation(request.POST, True, accommodation)
    accommodation.save()
    serializers = AccommodationSerializer(accommodation)
    return Response(serializers.data)

@extend_schema(
    summary="Cancel reservation",
    description="Cancel a reservation and update accommodation availability.",
    parameters=[
        OpenApiParameter(name="reservation_id", type=int, required=True),
    ],
    responses={
        200: OpenApiResponse(description='Reservation canceled successfully'),
        404: OpenApiResponse(description='No matching reservation found'),
        500: OpenApiResponse(description='Error cancelling reservation'),
    }
)
def api_cancel_reservation(request):
    """Epic 4.1 Cancel Reservation."""
    if request.method == 'GET':
        reservation_id = request.GET.get("reservation_id")
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

@extend_schema(
    summary="View active reservations",
    description="Get a list of all active (pending or confirmed) reservations.",
    responses={
        200: ReservationSerializer(many=True),
        405: OpenApiResponse(description='Invalid request method'),
    }
)
def api_view_active_reservations(request):
    """Epic 4.2 View Active Reservations."""
    if request.method == 'GET':
        # Fetch active reservations
        active_reservations = Reservation.objects.filter(status__in=['pending', 'confirmed'])
        serializer = ReservationSerializer(active_reservations, many=True)
        return JsonResponse({'reservations': serializer.data})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
