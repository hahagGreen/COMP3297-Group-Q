# UniHaven Database Documentation

## Database Structure

### Overview
The UniHaven database manages university student accommodations, including owner records, building details with standardized geo-addresses, and user contact information. It consists of 7 main tables with relationships that enforce data integrity and support accommodation ratings and distance calculations.

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
| geo_address | TEXT   |                  | Standardized address       |

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
| unit             | TEXT   |                                                | Unit or flat designation   |
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
| comment        | TEXT   |                                                | Optional feedback          |
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
   - **Activates**: AFTER INSERT ON Reservation
   - **Action**: Sets `is_reserved` to 1 on the associated Accommodation.

2. **update_accommodation_reserved_delete**
   - **Activates**: AFTER DELETE ON Reservation
   - **Action**: Sets `is_reserved` to 0 on the associated Accommodation.

3. **update_accommodation_rating_insert**
   - **Activates**: AFTER INSERT ON Rating
   - **Action**: Updates `average_rating` and `rating_count` on the associated Accommodation.

4. **update_accommodation_rating_delete**
   - **Activates**: AFTER DELETE ON Rating
   - **Action**: Recalculates `average_rating` and decrements `rating_count` on the associated Accommodation.

## Database Helper Functions

### User Management
#### register_user(name, email, password, role, phone=None)
Creates a new user in the system.

- **Parameters**:
  - `name` (string): User's full name
  - `email` (string): User's email address (must be unique)
  - `password` (string): User's password (hashed)
  - `role` (string): Either 'Student' or 'Specialist'
  - `phone` (string, optional): User's phone number
- **Returns**: `user_id` (integer) or None if failed

### Owner Management
#### add_owner(name, phone)
Creates a new owner.

- **Parameters**:
  - `name` (string): Owner's full name
  - `phone` (string): Owner's phone number
- **Returns**: `owner_id` (integer) or None if failed

### Building Management
#### add_building(name, latitude, longitude, address, geo_address=None)
Creates a new building.

- **Parameters**:
  - `name` (string): Building name
  - `latitude` (float): Latitude coordinate
  - `longitude` (float): Longitude coordinate
  - `address` (string): Physical address
  - `geo_address` (string, optional): Standardized address
- **Returns**: `building_id` (integer) or None if failed

### Accommodation Management
#### add_accommodation(availability_start, availability_end, type, beds, bedrooms, price, building_id, owner_id, unit=None)
Creates a new accommodation listing.

- **Parameters**:
  - `availability_start` (string): Start date
  - `availability_end` (string): End date
  - `type` (string): 'Room', 'Flat', or 'Mini hall'
  - `beds` (integer): Number of beds
  - `bedrooms` (integer): Number of bedrooms
  - `price` (float): Rental price
  - `building_id` (integer): Reference to Building
  - `owner_id` (integer): Reference to Owner
  - `unit` (string, optional): Unit designation
- **Returns**: `accommodation_id` (integer) or None if failed

#### get_accommodation_with_rating(accommodation_id)
Retrieves accommodation details with rating and building information.

- **Parameters**:
  - `accommodation_id` (integer): ID of the accommodation
- **Returns**: Dictionary with accommodation details or None

### Campus Management
#### add_campus(name, latitude, longitude)
Adds a new campus.

- **Parameters**:
  - `name` (string): Campus name
  - `latitude` (float): Latitude coordinate
  - `longitude` (float): Longitude coordinate
- **Returns**: `campus_id` (integer) or None if failed

### Reservation Management
#### make_reservation(user_id, accommodation_id, status='pending')
Creates a new reservation.

- **Parameters**:
  - `user_id` (integer): Student's ID
  - `accommodation_id` (integer): Accommodation's ID
  - `status` (string, optional): Initial status (default: 'pending')
- **Returns**: `reservation_id` (integer) or None if failed

#### update_reservation_status(reservation_id, status)
Updates reservation status.

- **Parameters**:
  - `reservation_id` (integer): Reservation ID
  - `status` (string): New status
- **Returns**: True if successful, False otherwise

### Rating System
#### add_rating(reservation_id, rating, comment=None)
Adds a rating for a completed reservation.

- **Parameters**:
  - `reservation_id` (integer): Reservation ID
  - `rating` (integer): Score (0-5)
  - `comment` (string, optional): Feedback
- **Returns**: `rating_id` (integer) or None if failed

### Statistics
#### get_stats()
Retrieves database statistics.

- **Returns**: Dictionary with counts of users, owners, buildings, accommodations, reservations, and ratings.
```