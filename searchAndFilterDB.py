import sqlite3
import requests
import xml.etree.ElementTree as ET
import math

def search(
    accommodation_type,
    availability_start,
    availability_end,
    min_beds,
    min_bedrooms,
    max_price
):
    """Search accommodations with specified filters."""
    conn = sqlite3.connect('unihaven.db')
    cursor = conn.cursor()

    # Base query with WHERE 1=1 to dynamically add conditions
    query = '''
    SELECT * 
    FROM Accommodation
    WHERE 1=1
    '''
    params = []

    # Add filters dynamically
    if accommodation_type:
        query += ' AND type = ?'
        params.append(accommodation_type)
    if availability_start and availability_end:
        query += ' AND availability_start <= ? AND availability_end >= ?'
        params.extend([availability_end, availability_start])
    if min_beds is not None and min_beds > 0:
        query += ' AND beds >= ?'
        params.append(min_beds)
    if min_bedrooms is not None and min_bedrooms > 0:
        query += ' AND bedrooms >= ?'
        params.append(min_bedrooms)
    if max_price is not None and max_price > 0:
        query += ' AND price <= ?'
        params.append(max_price)

    # Execute query
    cursor.execute(query, params)
    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return results

def getCampusCoords(campus_name):
    """Get the Campus Coordinates """
    conn = sqlite3.connect('unihaven.db')
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
        
        # Parse XML/JSON response
        root = ET.fromstring(response.content)
        lat = root.find('.//Latitude').text
        lon = root.find('.//Longitude').text
        return float(lat), float(lon)
    except Exception as e:
        print(f"Geocoding failed for '{address}': {str(e)}")
        return None, None

def calcDistance(lat1, lon1, lat2, lon2):
    """Calculate line of sight distances using equirectangular approximation. """
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
    return math.sqrt(x**2 + y**2) * 6371  # Earth radius

def sortDistance(accommodations, campus_name):
    """Sort accommodations by distance from specified campus."""
    try:
        campus_lat, campus_lon = getCampusCoords(campus_name)
    except ValueError as e:
        print(e)
        return accommodations
    
    for acc in accommodations:
        # Use existing coordinates or geocode if missing
        if not acc.get('latitude') or not acc.get('longitude'):
            acc_lat, acc_lon = getGeocodeByAddress(acc['address'])
            acc['latitude'] = acc_lat
            acc['longitude'] = acc_lon
        
        # Calculate distance
        acc['distance'] = calcDistance(
            acc.get('latitude'), acc.get('longitude'),
            campus_lat, campus_lon
        )
    
    # Sort by distance ascending
    return sorted(accommodations, key=lambda x: x['distance'])

# Example usage
if __name__ == "__main__":
    # Input Search Parameters
    accommodation_type = input("Enter accommodation type (Room, Flat, Mini-Hall): ")
    availability_start = input("Enter availability start date, Format: yyyy-mm-dd: ")
    availability_end = input("Enter availability end date, Format: yyyy-mm-dd: ")
    min_beds = input("Enter minimum number of beds: ")
    min_bedrooms = input("Enter minimum number of bedrooms: ")
    max_price = input("Enter maximum price: ")

    filtered = search(
        str(accommodation_type),
        str(availability_start),
        str(availability_end),
        int(min_beds),
        int(min_bedrooms),
        int(max_price)
    )
    
    # Sort by distance from Main Campus
    sortedAccommodations = sortDistance(filtered, "Main Campus")
    
    print(f"Found {len(sortedAccommodations)} accommodations:")
    for idx, acc in enumerate(sortedAccommodations, 1):
        print(f"{idx}. {acc['address']}")
        print(f"   Distance: {acc.get('distance', 'N/A'):.2f} km")
        print(f"   Price: HKD {acc['price']:.2f}\n")