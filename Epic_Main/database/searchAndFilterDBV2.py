import sqlite3
import requests # Keep for geocoding fallback, though less likely needed
import xml.etree.ElementTree as ET # Keep for geocoding fallback
import math
import os

# Use the V5 database name
DB_NAME = 'unihaven_sprint3.db'

def get_db_connection():
    """Get a connection to the V5 database."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, DB_NAME)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database {db_path}: {e}")
        raise


def search_accommodations( # Renamed for clarity
    accommodation_type=None,
    availability_start=None,
    availability_end=None,
    min_beds=None,
    min_bedrooms=None,
    max_price=None,
    campus_name=None, # Added optional campus filter
    max_distance_km=None # Added optional distance filter
):
    """Search accommodations based on V5 schema with optional campus proximity."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Base query: Select accommodations that are not reserved
    # Join with AccommodationOffering and potentially Campus if filtering by campus/distance
    select_clause = "SELECT DISTINCT A.* FROM Accommodation A" # Use DISTINCT as offerings might create duplicates
    join_clause = ""
    where_clauses = ["A.is_reserved = 0"]
    params = []

    # Add campus/distance filtering logic
    campus_lat, campus_lon = None, None
    if campus_name:
        try:
            campus_lat, campus_lon = getCampusCoords(campus_name) # Get coords early for potential distance calc
            # We need to join to find accommodations offered near this campus
            join_clause += """
            JOIN AccommodationOffering AO ON A.accommodation_id = AO.accommodation_id
            JOIN Campus C ON AO.campus_id = C.campus_id
            """
            where_clauses.append("C.name = ?")
            params.append(campus_name)
        except ValueError as e:
            print(f"Warning: {e}. Proceeding without campus filter.")
            campus_name = None # Reset campus_name if not found


    # Add standard filters
    if accommodation_type:
        where_clauses.append('A.type = ?')
        params.append(accommodation_type)
    if availability_start and availability_end:
        where_clauses.append('A.availability_start <= ? AND A.availability_end >= ?')
        params.extend([availability_start, availability_end])
    if min_beds is not None and min_beds > 0:
        where_clauses.append('A.beds >= ?')
        params.append(min_beds)
    if min_bedrooms is not None and min_bedrooms > 0:
        where_clauses.append('A.bedrooms >= ?')
        params.append(min_bedrooms)
    if max_price is not None and max_price > 0:
        where_clauses.append('A.price <= ?')
        params.append(max_price)

    # Construct the final query
    query = f"{select_clause} {join_clause} WHERE {' AND '.join(where_clauses)}"

    # Execute the query
    try:
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()] # Convert Row objects to dicts
    except sqlite3.Error as e:
        print(f"Error executing search query: {e}")
        results = []
    finally:
        cursor.close()
        conn.close()

    # --- Post-query distance filtering and sorting ---
    if campus_lat is not None and campus_lon is not None:
        # Calculate distance for all results (even if campus wasn't in the SQL filter)
        for acc in results:
            acc['distance'] = calcDistance(
                acc.get('latitude'), acc.get('longitude'),
                campus_lat, campus_lon
            )

        # Filter by max_distance_km if provided
        if max_distance_km is not None and max_distance_km > 0:
            results = [acc for acc in results if acc['distance'] <= max_distance_km]

        # Sort by distance
        results.sort(key=lambda x: x['distance'])

    return results


def getCampusCoords(campus_name):
    """Get coordinates for a given campus name from the V5 database."""
    conn = get_db_connection() # Uses the V5 DB connection
    cursor = conn.cursor()
    try:
        cursor.execute(
            'SELECT latitude, longitude FROM Campus WHERE name = ?',
            (campus_name,)
        )
        result = cursor.fetchone()
    except sqlite3.Error as e:
         print(f"Database error fetching campus '{campus_name}': {e}")
         result = None
    finally:
        cursor.close()
        conn.close()

    if not result:
        raise ValueError(f"Campus '{campus_name}' not found in database '{DB_NAME}'")
    # Access by column name due to row_factory
    return result['latitude'], result['longitude']


def getGeocodeByAddress(address):
    """Fallback: Use external service if needed (less likely with V5 schema)."""
    # This function remains the same, but should be used less often
    # as V5 Accommodation table has mandatory lat/lon.
    try:
        # Add a user-agent? Some APIs might require it.
        headers = {'User-Agent': 'UniHavenApp/1.0'}
        response = requests.get(
            'https://www.als.gov.hk/lookup',
            params={'q': address},
            timeout=10,
            headers=headers
        )
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        # Check content type before parsing
        if 'application/xml' not in response.headers.get('Content-Type', ''):
             print(f"Warning: Unexpected content type from geocoder for '{address}'. Expected XML.")
             # Try parsing anyway, might work or fail gracefully
             # Alternatively return None, None here

        root = ET.fromstring(response.content)
        # Find the first 'SuggestedAddress' -> 'Address' -> 'PremisesAddress'
        premises_address = root.find('.//Address/PremisesAddress')
        if premises_address is not None:
            lat = premises_address.find('.//Latitude').text
            lon = premises_address.find('.//Longitude').text
            if lat and lon:
                return float(lat), float(lon)
        # Fallback if specific structure isn't found (might need adjustment based on API response)
        lat_elem = root.find('.//Latitude')
        lon_elem = root.find('.//Longitude')
        if lat_elem is not None and lon_elem is not None and lat_elem.text and lon_elem.text:
            print(f"Warning: Used fallback lat/lon parsing for '{address}'")
            return float(lat_elem.text), float(lon_elem.text)

        print(f"Geocoding failed for '{address}': Latitude/Longitude not found in response.")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"Geocoding network error for '{address}': {str(e)}")
        return None, None
    except ET.ParseError as e:
        print(f"Geocoding XML parsing error for '{address}': {str(e)}")
        return None, None
    except Exception as e: # Catch other potential errors (e.g., float conversion)
        print(f"Geocoding unexpected error for '{address}': {str(e)}")
        return None, None


def calcDistance(lat1, lon1, lat2, lon2):
    """Calculate distance using Haversine formula for better accuracy."""
    # V5 schema guarantees lat/lon are NOT NULL REALs in Accommodation and Campus
    if None in (lat1, lon1, lat2, lon2):
        # This case should ideally not happen if data comes from DB
        print("Warning: calcDistance received None coordinates.")
        return float('inf')

    R = 6371.0  # Earth radius in kilometers

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

# sortDistance is integrated into search_accommodations now

# --- Example Usage (Updated for V3) ---
if __name__ == "__main__":
    print(f"--- Accommodation Search V3 (Database: {DB_NAME}) ---")

    # Input search parameters
    accommodation_type = input("Enter accommodation type (Room, Flat, Mini hall) [Leave blank for any]: ")
    availability_start = input("Enter availability start date (YYYY-MM-DD) [Leave blank for any]: ")
    availability_end = input("Enter availability end date (YYYY-MM-DD) [Leave blank for any]: ")
    min_beds_str = input("Enter minimum number of beds [Leave blank for any]: ")
    min_bedrooms_str = input("Enter minimum number of bedrooms [Leave blank for any]: ")
    max_price_str = input("Enter maximum price [Leave blank for any]: ")
    target_campus = input("Enter target campus name for proximity sort/filter [Leave blank to skip]: ")
    max_distance_str = ""
    if target_campus.strip():
        max_distance_str = input(f"Enter max distance from {target_campus} in km [Leave blank for any]: ")


    # Convert inputs, handling empty values gracefully
    try:
        min_beds = int(min_beds_str) if min_beds_str.strip() else None
        min_bedrooms = int(min_bedrooms_str) if min_bedrooms_str.strip() else None
        max_price = float(max_price_str) if max_price_str.strip() else None # Use float for price
        max_distance = float(max_distance_str) if max_distance_str.strip() else None
    except ValueError:
        print("Invalid numeric input. Treating as 'any'.")
        min_beds, min_bedrooms, max_price, max_distance = None, None, None, None

    # Use the updated search function
    results = search_accommodations(
        accommodation_type=accommodation_type.strip() or None,
        availability_start=availability_start.strip() or None,
        availability_end=availability_end.strip() or None,
        min_beds=min_beds,
        min_bedrooms=min_bedrooms,
        max_price=max_price,
        campus_name=target_campus.strip() or None,
        max_distance_km=max_distance
    )

    print(f"\n--- Search Results ({len(results)} found) ---")
    if not results:
        print("No accommodations found matching your criteria.")
    else:
        # Display results (already sorted by distance if campus was specified)
        for idx, acc in enumerate(results, 1):
            print(f"\n{idx}. Accommodation ID: {acc['accommodation_id']}")
            print(f"   Type: {acc['type']}, Beds: {acc['beds']}, Bedrooms: {acc['bedrooms']}")
            print(f"   Price: HKD {acc['price']:.2f}")
            print(f"   Address: {acc['address']}")
            print(f"   Building: {acc.get('building_name', 'N/A')}") # get() for safety
            print(f"   Availability: {acc['availability_start']} to {acc['availability_end']}")
            print(f"   Owner: {acc.get('owner_name', 'N/A')}, Contact: {acc.get('owner_contact', 'N/A')}")
            print(f"   Rating: {acc.get('average_rating', 0):.1f}/5 ({acc.get('rating_count', 0)} ratings)")
            # Display distance if calculated
            if 'distance' in acc:
                distance_str = 'N/A' if math.isinf(acc['distance']) else f"{acc['distance']:.2f} km"
                print(f"   Distance from {target_campus}: {distance_str}")
