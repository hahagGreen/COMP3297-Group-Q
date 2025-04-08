from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from .models import Accommodation
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