from django.shortcuts import render, HttpResponse, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import generics, status
from django.http import JsonResponse
from .models import Accommodation, Specialist, Reservation
import json
import requests
from .serializers import SpecialistAccommodationSerializer, SpecialistReservationSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.core.mail import send_mail

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
    accommodation.building_name = data.get("buildingName")
    accommodation.owner_name = data.get("ownerName")
    accommodation.owner_contact = data.get("ownerContact")
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
    
@extend_schema(
    summary="Add new accommodation",
    description="Add a new accommodation by a specialist",
    parameters=[
        OpenApiParameter(name="userId", type=int, location=OpenApiParameter.QUERY, required=True,
                         description='ID of the specialist user'),
        OpenApiParameter(name="startDate", type=str, location=OpenApiParameter.QUERY, required=True,
                         description='Availability start date (YYYY-MM-DD)'),
        OpenApiParameter(name="endDate", type=str, location=OpenApiParameter.QUERY, required=True,
                         description='Availability end date (YYYY-MM-DD)'),
        OpenApiParameter(name="type", type=str, location=OpenApiParameter.QUERY, required=True,
                         description='Type of accommodation', enum=['Room', 'Flat', 'Mini hall']),
        OpenApiParameter(name="beds", type=int, location=OpenApiParameter.QUERY, required=True,
                         description='Number of beds'),
        OpenApiParameter(name="bedrooms", type=int, location=OpenApiParameter.QUERY, required=True,
                         description='Number of bedrooms'),
        OpenApiParameter(name="price", type=float, location=OpenApiParameter.QUERY, required=True,
                         description='Price per night in HKD'),
        OpenApiParameter(name="buildingName", type=str, location=OpenApiParameter.QUERY, required=False,
                         description='Name of the building'),
        OpenApiParameter(name="address", type=str, location=OpenApiParameter.QUERY, required=True,
                         description='Physical address'),
        OpenApiParameter(name="ownerName", type=str, location=OpenApiParameter.QUERY, required=False,
                         description='Name of the owner'),
        OpenApiParameter(name="ownerContact", type=str, location=OpenApiParameter.QUERY, required=False,
                         description='Contact information of the owner'),
    ],
    responses={
        200: SpecialistAccommodationSerializer,
        404: OpenApiResponse(description='User not found or not a specialist'),
    }
)
class ApiAddView(generics.GenericAPIView):
    """Add a new accommodation by a specialist using URL parameters."""
    serializer_class = SpecialistAccommodationSerializer
    
    def post(self, request, *args, **kwargs):
        # Get data from URL parameters instead of form data
        userId = request.GET.get('userId')
        try:
            user = Specialist.objects.get(specialist_id=userId)
        except Specialist.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        accommodation = setAccommodation(request.GET)
        accommodation.save()
        serializer = self.get_serializer(accommodation)
        return Response(serializer.data)

@extend_schema(
    summary="Cancel reservation",
    description="Cancel an existing reservation via POST with URL parameter.",
    parameters=[
        OpenApiParameter(name="reservation_id", type=int, location=OpenApiParameter.QUERY, required=True),
    ],
    responses={
        200: OpenApiResponse(response=SpecialistReservationSerializer, description='Reservation canceled successfully'),
        400: OpenApiResponse(description='Reservation ID not provided'),
        404: OpenApiResponse(description='Reservation not found'),
        405: OpenApiResponse(description='Invalid request method'),
        500: OpenApiResponse(description='Server error'),
    }
)
class ApiCancelReservationView(generics.GenericAPIView):
    """Epic 4.1 Cancel reservation via POST with URL parameter."""
    serializer_class = SpecialistReservationSerializer

    def post(self, request, *args, **kwargs):
        reservation_id = request.GET.get("reservation_id")  # Get from URL query
        if not reservation_id:
            return JsonResponse({'error': 'Reservation ID not provided'}, status=400)
        
        try:
            reservation = Reservation.objects.get(reservation_id=reservation_id)
            reservation.status = Reservation.CANCELED
            reservation.save()  # Triggers save() to update Accommodation.is_reserved

            user = Specialist.objects.get(user_id=userID)

            send_mail(
                'Reservation Cancellation Confirmation',
                f'reservation #{reservation_id} for accommodation at {Accommodation.address} has been cancelled successfully',
                'noreplyhku0@gmail.com',
                [user.email],
                fail_silently=False,
            )

            send_mail(
                'Your Reservation has been cancelled',
                f'Your reservation #{reservation_id} for accommodation at {Accommodation.address} has been cancelled',
                'noreplyhku0@gmail.com',
                [reservation.user.email],
                fail_silently=False,
            )
            
            serializer = SpecialistReservationSerializer(reservation)
            return JsonResponse({'message': 'Reservation canceled successfully', 'data': serializer.data})
        
        except Reservation.DoesNotExist:
            return JsonResponse({'error': 'Reservation not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@extend_schema(
    summary="View active reservations",
    description="Fetch all active reservations for a given user.",
    responses={
        200: SpecialistReservationSerializer,
        404: OpenApiResponse(description='User not found'),
    }
)
@api_view(['GET'])
def api_view_active_reservations(request):
    """Epic 4.2 View Active Reservations."""
    if request.method == 'GET':
        # Fetch active reservations
        active_reservations = Reservation.objects.filter(status__in=['pending', 'confirmed'])
        serializer = SpecialistReservationSerializer(active_reservations, many=True)
        return JsonResponse({'reservations': serializer.data})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@extend_schema(
    summary="Modify reservation status",
    description="Modify the status of a reservation via POST with URL parameters.",
    parameters=[
        OpenApiParameter(name="reservation_id", type=int, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter(name="status", type=str, location=OpenApiParameter.QUERY, required=True),
    ],
    responses={
        200: OpenApiResponse(response=SpecialistReservationSerializer, description='Reservation status updated successfully'),
        400: OpenApiResponse(description='Invalid request'),
        404: OpenApiResponse(description='Reservation not found'),
        405: OpenApiResponse(description='Invalid request method'),
        500: OpenApiResponse(description='Server error'),
    }
)
class ApiModifyReservationView(generics.GenericAPIView):
    """Epic 4.3 Modify reservation status via POST with URL parameters."""
    serializer_class = SpecialistReservationSerializer
    
    def post(self, request, *args, **kwargs):
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
            
            if new_status == 'confirmed':
                # Update accommodation availability
                accommodation = reservation.accommodation
                accommodation.is_reserved = 1
                accommodation.save()
                # Send email notification to student

                send_mail(
                    'Your Reservation Status Update',
                    f'Your reservation #{reservation_id} for accommodation at {accommodation.address} has been {new_status}.',
                    'noreplyhku0@gmail.com',
                    [reservation.user.email],
                    fail_silently=False,
                )
            
            # Serialize the reservation for the response
            serializer = SpecialistReservationSerializer(reservation)
            return JsonResponse({
                'message': f'Reservation {reservation_id} status updated to {new_status}',
                'data': serializer.data
            })
        
        except Reservation.DoesNotExist:
            return JsonResponse({'error': 'Reservation not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
