import sqlite3
import requests
import xml.etree.ElementTree as ET
import math
import os

def search(
    accommodation_type,
    availability_start,
    availability_end,
    min_beds,
    min_bedrooms,
    max_price
):
    """Search accommodations with specified filters."""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the database file
    db_path = os.path.join(script_dir, "unihaven.db") # Use a new db name
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Base query filtering only available accommodations
    query = '''
    SELECT * 
    FROM Accommodation
    WHERE is_reserved = 0
    '''
    params = []

    # Add filters dynamically based on input
    if accommodation_type:
        # Ensure type matches the CHECK constraint: 'Room', 'Flat', 'Mini hall'
        query += ' AND type = ?'
        params.append(accommodation_type)
    if availability_start and availability_end:
        # Filter accommodations available for the entire requested period
        # availability_start <= user's start date AND availability_end >= user's end date
        query += ' AND availability_start <= ? AND availability_end >= ?'
        params.extend([availability_start, availability_end])
    if min_beds is not None and min_beds > 0:
        # Beds must be a positive integer as per schema
        query += ' AND beds >= ?'
        params.append(min_beds)
    if min_bedrooms is not None and min_bedrooms > 0:
        # Bedrooms must be a positive integer as per schema
        query += ' AND bedrooms >= ?'
        params.append(min_bedrooms)
    if max_price is not None and max_price > 0:
        # Price must be a positive real number as per schema
        query += ' AND price <= ?'
        params.append(max_price)

    # Execute the query with parameters
    cursor.execute(query, params)
    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return results

def getCampusCoords(campus_name):
    """Search accommodations with specified filters."""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the database file
    db_path = os.path.join(script_dir, "unihaven.db") # Use a new db name
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT latitude, longitude FROM Campus WHERE name = ?',
        (campus_name,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not result:
        raise ValueError(f"Campus '{campus_name}' not found")
    return result[0], result[1]

def getGeocodeByAddress(address):
    """Integrate data.gov.hk Address Lookup Service for latitude/longitude."""
    try:
        response = requests.get(
            'https://www.als.gov.hk/lookup',
            params={'q': address},
            timeout=10
        )
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        lat = root.find('.//Latitude').text
        lon = root.find('.//Longitude').text
        return float(lat), float(lon)
    except Exception as e:
        print(f"Geocoding failed for '{address}': {str(e)}")
        return None, None

def calcDistance(lat1, lon1, lat2, lon2):
    """Calculate line of sight distances using equirectangular approximation."""
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
    
    # Convert to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    
    # Equirectangular formula
    x = (lon2 - lon1) * math.cos((lat1 + lat2) / 2)
    y = lat2 - lat1
    return math.sqrt(x**2 + y**2) * 6371  # Earth radius in km

def sortDistance(accommodations, campus_name):
    """Sort accommodations by distance from specified campus."""
    try:
        campus_lat, campus_lon = getCampusCoords(campus_name)
    except ValueError as e:
        print(e)
        return accommodations
    
    for acc in accommodations:
        # Use existing coordinates (latitude and longitude are NOT NULL in schema)
        acc_lat = acc.get('latitude')
        acc_lon = acc.get('longitude')
        
        # Fallback to geocoding if coordinates are unexpectedly missing
        if acc_lat is None or acc_lon is None:
            acc_lat, acc_lon = getGeocodeByAddress(acc['address'])
            acc['latitude'] = acc_lat
            acc['longitude'] = acc_lon
        
        # Calculate distance
        acc['distance'] = calcDistance(
            acc_lat, acc_lon,
            campus_lat, campus_lon
        )
    
    # Sort by distance ascending
    return sorted(accommodations, key=lambda x: x['distance'])

# Example usage
if __name__ == "__main__":
    # Input search parameters
    accommodation_type = input("Enter accommodation type (Room, Flat, Mini hall): ")
    availability_start = input("Enter availability start date, Format: YYYY-MM-DD: ")
    availability_end = input("Enter availability end date, Format: YYYY-MM-DD: ")
    min_beds = input("Enter minimum number of beds: ")
    min_bedrooms = input("Enter minimum number of bedrooms: ")
    max_price = input("Enter maximum price: ")

    # Convert inputs, handling empty values gracefully
    try:
        min_beds = int(min_beds) if min_beds.strip() else 0
        min_bedrooms = int(min_bedrooms) if min_bedrooms.strip() else 0
        max_price = int(max_price) if max_price.strip() else 0
    except ValueError:
        print("Invalid input for beds, bedrooms, or price. Using defaults (0).")
        min_beds, min_bedrooms, max_price = 0, 0, 0

    filtered = search(
        accommodation_type,
        availability_start,
        availability_end,
        min_beds,
        min_bedrooms,
        max_price
    )
    
    # Sort by distance from Main Campus
    sorted_accommodations = sortDistance(filtered, "Main Campus")
    
    print(f"Found {len(sorted_accommodations)} accommodations:")
    for idx, acc in enumerate(sorted_accommodations, 1):
        distance = acc.get('distance', float('inf'))
        distance_str = 'N/A' if math.isinf(distance) else f"{distance:.2f} km"
        print(f"{idx}. {acc['address']}")
        print(f"   Distance: {distance_str}")
        print(f"   Price: HKD {acc['price']:.2f}\n")