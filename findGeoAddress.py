# Epic 3: Accommodation details & geolocation   

# Priority: 3 (Sprint 1)   

# User stories:   

# As an HKU member, I want to view accommodation details, such as price, beds, location, etc., so that I can make informed decisions when selecting suitable housing options.  

# As a CEDARS specialist, I want to add accommodation with geolocation data so that HKU members can select accommodation based on location.   

# Notes:   

# Automatically fetch latitude/longitude via data.gov.hk API.   

# Store HKU campus coordinates (pre provided).   
import requests
import json

# Fetch coordinates from the API
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

# Example usage of fetch_coordinates and getGeoAddress 
# test with a valid address
if __name__ == "__main__":
    while(True):
        location = str(input("Enter the location: "))
        if(location == ""):
            break
        result, status = fetch_coordinates(location)
        if status == 200:
            geogAddr, latitude, longitude = getGeoAddress(json.loads(result.text))
            print(f"""Location data for {location}:\n
            GeoAddress: {geogAddr}\n
            Latitude: {latitude}\n
            Longitude: {longitude}\n
                """)   
        elif status == 404:
            print("Location not found.")
        else:
            print(f"Error: {status}")
    
    