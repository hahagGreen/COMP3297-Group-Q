from django.shortcuts import render, HttpResponse, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from .models import Accommodation, User 
import json
import requests
from .serializers import AccommodationSerializer
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
