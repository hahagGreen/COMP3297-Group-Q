# Accommodation Search API Documentation

This API allows clients to search for accommodations based on various filters such as type, availability, number of beds, bedrooms, price, and proximity to a campus. The response is returned in JSON format.

## Base URL
```
http://localhost:8000/accommodations/api/search/
```

## Endpoint

### **GET /search/**
Retrieve a list of accommodations matching the specified filters.

#### **Request**
- **Method**: `GET`
- **URL**: `/accommodations/api/search/`
- **Query Parameters**:
  All parameters are optional. If omitted, the API returns all accommodations without filtering (unless sorted by campus distance).

  | Parameter            | Type    | Description                                                                 | Example Value       |
  |----------------------|---------|-----------------------------------------------------------------------------|---------------------|
  | `accommodation_type` | String  | Type of accommodation (e.g., "Room", "Flat", "Mini-Hall")                  | `Room`              |
  | `availability_start` | Date    | Start date of availability (format: `YYYY-MM-DD`)                          | `2023-01-01`       |
  | `availability_end`   | Date    | End date of availability (format: `YYYY-MM-DD`)                            | `2023-12-31`       |
  | `min_beds`           | Integer | Minimum number of beds (default = 1, must be ≥ 1)                                       | `2`                 |
  | `min_bedrooms`       | Integer | Minimum number of bedrooms (defalt = 1, must be ≥ 1)                                   | `1`                 |
  | `max_price`          | Float   | Maximum price in HKD (must be ≥ 0)                                         | `6000.00`           |
  | `campus`             | Integer | Campus ID to sort results by distance (fetches from `Campus` table)        | `1`                 |
  | `is_reserved`             | Boolean | Show reservation available accommodations only (defaul = 0)        | `1`                 |

#### **Response**
- **Content-Type**: `application/json`
- **Status Codes**:
  - `200 OK`: Successful response with accommodation data.
  - `400 Bad Request`: Invalid parameters provided, with error details.

##### **Success Response (200 OK)**
```json
{
  "filters": [
    "Type: Room",
    "Minimum Beds: 2",
    "Sorted by distance from: Main Campus"
  ],
  "accommodations": [
    {
      "id": 1,
      "type": "Room",
      "availability_start": "2023-01-01",
      "availability_end": "2023-12-31",
      "beds": 2,
      "bedrooms": 1,
      "price": 5000.00,
      "address": "123 Example St, Hong Kong",
      "latitude": 22.3193,
      "longitude": 114.1694,
      "geo_address": "123 Example St, Hong Kong",
      "is_reserved": false,
      "distance": 1.25
    },
    {
      "id": 2,
      "type": "Room",
      "availability_start": "2023-02-01",
      "availability_end": "2023-11-30",
      "beds": 3,
      "bedrooms": 1,
      "price": 6000.00,
      "address": "456 Sample Rd, Hong Kong",
      "latitude": 22.3160,
      "longitude": 114.1720,
      "geo_address": "456 Sample Rd, Hong Kong",
      "is_reserved": true,
      "distance": 1.80
    }
  ]
}
```

- **Response Fields**:
  - `filters`: Array of strings describing the applied filters.
  - `accommodations`: Array of accommodation objects with the following properties:
    - `id`: Integer, unique identifier for the accommodation.
    - `type`: String, type of accommodation.
    - `availability_start`: String, start date of availability (ISO 8601 format: `YYYY-MM-DD`).
    - `availability_end`: String, end date of availability (ISO 8601 format: `YYYY-MM-DD`).
    - `beds`: Integer, number of beds.
    - `bedrooms`: Integer, number of bedrooms.
    - `price`: Float, price in HKD.
    - `address`: String, physical address.
    - `latitude`: Float, latitude coordinate.
    - `longitude`: Float, longitude coordinate.
    - `geo_address`: String, geocoded address (may match `address`).
    - `is_reserved`: Boolean, indicates if the accommodation is reserved.
    - `distance`: Float or null, distance in kilometers from the specified campus (included only if `campus` is provided).

##### **Error Response (400 Bad Request)**
```json
{
  "errors": {
    "min_beds": ["Ensure this value is greater than or equal to 1."]
  }
}
```
- `errors`: Object containing field-specific error messages.

#### **Example Requests**

1. **Search for rooms with at least 2 beds near campus ID 1**:
   ```
   GET /accommodations/api/search/?accommodation_type=Room&min_beds=2&campus=1
   ```

2. **Search for flats available between Jan 1 and Dec 31, 2023, under HKD 7000**:
   ```
   GET /accommodations/api/search/?accommodation_type=Flat&availability_start=2023-01-01&availability_end=2023-12-31&max_price=7000
   ```

3. **Get all accommodations without filters**:
   ```
   GET /accommodations/api/search/
   ```

## Notes
- **Distance Calculation**: When `campus` is provided, accommodations are sorted by distance from the campus using an equirectangular approximation. Distances are in kilometers and included in the response.
- **Geocoding**: If an accommodation lacks latitude/longitude, the API attempts to geocode its address using the DATA.GOV.HK API and saves the coordinates for future requests.
- **Availability**: The `is_reserved` field indicates current reservation status, but the API does not filter out reserved accommodations by default.
- **Validation**: Parameters are validated (e.g., `min_beds` must be ≥ 1). Invalid inputs return a 400 error with details.
