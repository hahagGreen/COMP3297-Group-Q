# UniHaven Database Documentation

## Database Structure

### Overview
The UniHaven database is designed to manage university student accommodations, including owner records, building details, and user contact information. It consists of 7 main tables with relationships that enforce data integrity and support accommodation ratings and distance calculations.

### Entity Relationship Diagram

```
User (1) -----< Reservation (1) >----- (1) Accommodation (N) ---- (1) Building
                     |                            |     |
                     | (0..1)                     |     | (N)
                     v                            |     +---- (1) Owner
                   Rating ------------------------+
                   
Campus (standalone for reference data)
```

### Tables

#### User
Stores information about system users (students and specialists).

| Field    | Type   | Constraints                                  | Description          |
|----------|--------|----------------------------------------------|----------------------|
| user_id  | INTEGER| PRIMARY KEY                                  | Unique identifier    |
| name     | TEXT   | NOT NULL                                     | Full name            |
| email    | TEXT   | NOT NULL, UNIQUE                             | Email address        |
| password | TEXT   | NOT NULL                                     | Hashed password      |
| role     | TEXT   | NOT NULL, CHECK(role IN ('Student', 'Specialist')) | User role      |
| phone    | TEXT   |                                              | Contact phone number |

#### Owner
Stores information about accommodation owners.

| Field    | Type   | Constraints      | Description          |
|----------|--------|------------------|----------------------|
| owner_id | INTEGER| PRIMARY KEY      | Unique identifier    |
| name     | TEXT   | NOT NULL         | Owner's full name    |
| phone    | TEXT   | NOT NULL         | Owner's phone number |

#### Building
Stores information about buildings where accommodations are located.

| Field       | Type   | Constraints      | Description                |
|-------------|--------|------------------|----------------------------|
| building_id | INTEGER| PRIMARY KEY      | Unique identifier          |
| name        | TEXT   | NOT NULL         | Building name              |
| latitude    | REAL   | NOT NULL         | Latitude coordinate        |
| longitude   | REAL   | NOT NULL         | Longitude coordinate       |
| address     | TEXT   | NOT NULL         | Physical address           |

#### Accommodation
Stores information about available housing options.

| Field            | Type   | Constraints                                    | Description                |
|------------------|--------|------------------------------------------------|----------------------------|
| accommodation_id | INTEGER| PRIMARY KEY                                    | Unique identifier          |
| availability_start| TEXT  | NOT NULL                                       | Start date of availability |
| availability_end | TEXT   | NOT NULL                                       | End date of availability   |
| type             | TEXT   | NOT NULL, CHECK(type IN ('Room', 'Flat', 'Mini hall')) | Accommodation type |
| beds             | INTEGER| NOT NULL, CHECK(beds > 0)                      | Number of beds             |
| bedrooms         | INTEGER| NOT NULL, CHECK(bedrooms > 0)                  | Number of bedrooms         |
| price            | REAL   | NOT NULL, CHECK(price > 0)                     | Rental price               |
| building_id      | INTEGER| NOT NULL, FOREIGN KEY (Building.building_id)   | Reference to Building      |
| owner_id         | INTEGER| NOT NULL, FOREIGN KEY (Owner.owner_id)         | Reference to Owner         |
| is_reserved      | INTEGER| NOT NULL, DEFAULT 0, CHECK(is_reserved IN (0, 1)) | Reservation status      |
| average_rating   | REAL   | DEFAULT 0                                      | Average rating             |
| rating_count     | INTEGER| DEFAULT 0                                      | Number of ratings          |

#### Reservation
Manages bookings of accommodations by students.

| Field            | Type   | Constraints                                    | Description                |
|------------------|--------|------------------------------------------------|----------------------------|
| reservation_id   | INTEGER| PRIMARY KEY                                    | Unique identifier          |
| user_id          | INTEGER| NOT NULL, FOREIGN KEY (User.user_id)           | Reference to User          |
| accommodation_id | INTEGER| NOT NULL, UNIQUE, FOREIGN KEY (Accommodation.accommodation_id) | Reference to Accommodation |
| status           | TEXT   | NOT NULL, CHECK(status IN ('pending', 'confirmed', 'canceled', 'completed')) | Reservation status |

#### Rating
Stores feedback from students about accommodations.

| Field          | Type   | Constraints                                    | Description                |
|----------------|--------|------------------------------------------------|----------------------------|
| rating_id      | INTEGER| PRIMARY KEY                                    | Unique identifier          |
| reservation_id | INTEGER| NOT NULL, UNIQUE, FOREIGN KEY (Reservation.reservation_id) | Reference to Reservation |
| rating         | INTEGER| NOT NULL, CHECK(rating BETWEEN 0 AND 5)        | Numerical score (0-5)      |
| date           | TEXT   | NOT NULL                                       | Date of rating submission  |

#### Campus
Stores HKU campus locations for distance calculations.

| Field     | Type   | Constraints      | Description          |
|-----------|--------|------------------|----------------------|
| campus_id | INTEGER| PRIMARY KEY      | Unique identifier    |
| name      | TEXT   | NOT NULL         | Campus name          |
| latitude  | REAL   | NOT NULL         | Latitude coordinate  |
| longitude | REAL   | NOT NULL         | Longitude coordinate |

### Triggers

1. **update_accommodation_reserved_insert**
   - Activates: AFTER INSERT ON Reservation
   - Action: Sets `is_reserved` to 1 on the associated Accommodation

2. **update_accommodation_reserved_delete**
   - Activates: AFTER DELETE ON Reservation 
   - Action: Sets `is_reserved` to 0 on the associated Accommodation

3. **update_accommodation_rating_insert**
   - Activates: AFTER INSERT ON Rating
   - Action: Updates `average_rating` and `rating_count` on the associated Accommodation

4. **update_accommodation_rating_delete**
   - Activates: AFTER DELETE ON Rating
   - Action: Updates `average_rating` and `rating_count` on the associated Accommodation

## Database Helper Functions

### User Management

#### register_user(name, email, password, role, phone)
Creates a new user in the system.

**Parameters:**
- `name` (string): User's full name
- `email` (string): User's email address (must be unique)
- `password` (string): User's password (should be hashed before storage)
- `role` (string): Either 'Student' or 'Specialist'
- `phone` (string): User's phone number

**Returns:**
- Integer: `user_id` of the created user, or None if failed

**Example:**
```python
user_id = register_user("John Doe", "john.doe@example.com", "hashed_password123", "Student", "123-456-7890")
if user_id:
    print(f"Created user with ID: {user_id}")
```

### Owner Management

#### add_owner(name, phone)
Creates a new owner in the system.

**Parameters:**
- `name` (string): Owner's full name
- `phone` (string): Owner's phone number

**Returns:**
- Integer: `owner_id` of the created owner, or None if failed

**Example:**
```python
owner_id = add_owner("Jane Smith", "987-654-3210")
if owner_id:
    print(f"Created owner with ID: {owner_id}")
```

### Building Management

#### add_building(name, latitude, longitude, address)
Creates a new building in the system.

**Parameters:**
- `name` (string): Building name
- `latitude` (float): Latitude coordinate
- `longitude` (float): Longitude coordinate
- `address` (string): Physical address

**Returns:**
- Integer: `building_id` of the created building, or None if failed

**Example:**
```python
building_id = add_building("Building 1", 22.283454, 114.137432, "123 Main St, Central, HK")
if building_id:
    print(f"Created building with ID: {building_id}")
```

### Accommodation Management

#### add_accommodation(availability_start, availability_end, type, beds, bedrooms, price, building_id, owner_id)
Creates a new accommodation listing.

**Parameters:**
- `availability_start` (string): Start date of availability
- `availability_end` (string): End date of availability
- `type` (string): Accommodation type ('Room', 'Flat', 'Mini hall')
- `beds` (integer): Number of beds
- `bedrooms` (integer): Number of bedrooms
- `price` (float): Rental price
- `building_id` (integer): Reference to Building
- `owner_id` (integer): Reference to Owner

**Returns:**
- Integer: `accommodation_id` of the created accommodation, or None if failed

**Example:**
```python
acc_id = add_accommodation("2024-01-01", "2025-01-01", "Room", 1, 1, 8000.0, 1, 1)
if acc_id:
    print(f"Created accommodation with ID: {acc_id}")
```

#### get_accommodation_with_rating(accommodation_id)
Retrieves an accommodation with its rating and building information.

**Parameters:**
- `accommodation_id` (integer): ID of the accommodation to retrieve

**Returns:**
- Dictionary with accommodation details, including `average_rating`, `rating_count`, and building details

**Example:**
```python
acc_details = get_accommodation_with_rating(5)
if acc_details:
    print(f"Accommodation ID: {acc_details['accommodation_id']}")
    print(f"Building: {acc_details['building_name']}")
    print(f"Rating: {acc_details['average_rating']} ({acc_details['rating_count']} reviews)")
```

### Reservation Management

#### make_reservation(user_id, accommodation_id, status='pending')
Creates a new reservation for an accommodation.

**Parameters:**
- `user_id` (integer): ID of the student making the reservation
- `accommodation_id` (integer): ID of the accommodation to reserve
- `status` (string, optional): Initial status (default: 'pending')

**Returns:**
- Integer: `reservation_id` of the created reservation, or None if failed

**Example:**
```python
reservation_id = make_reservation(user_id=1, accommodation_id=5)
```

### Rating System

#### add_rating(reservation_id, rating)
Adds a rating for a completed reservation.

**Parameters:**
- `reservation_id` (integer): ID of the reservation to rate
- `rating` (integer): Numerical score (0-5)

**Returns:**
- Integer: `rating_id` of the created rating, or None if failed

**Example:**
```python
rating_id = add_rating(reservation_id=3, rating=4)
```