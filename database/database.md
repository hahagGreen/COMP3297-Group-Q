# UniHaven Database Documentation

## Database Structure

### Overview
The UniHaven database is designed to manage university student accommodations. It consists of 5 main tables with relationships that enforce data integrity and direct rating information on accommodations.

### Entity Relationship Diagram

```
User (1) -----< Reservation (1) >----- (1) Accommodation
                     |                        |
                     | (0..1)                 | (Aggregated ratings)
                     v                        |
                   Rating --------------------+
                   
Campus (standalone for reference data)
```

### Tables

#### User
Stores information about system users (students and specialists).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| user_id | INTEGER | PRIMARY KEY | Unique identifier |
| name | TEXT | NOT NULL | Full name |
| email | TEXT | NOT NULL, UNIQUE | Email address (used for login) |
| password | TEXT | NOT NULL | Hashed password |
| role | TEXT | NOT NULL, CHECK(role IN ('Student', 'Specialist')) | User role |

#### Accommodation
Stores information about available housing options.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| accommodation_id | INTEGER | PRIMARY KEY | Unique identifier |
| availability_start | TEXT | NOT NULL | Start date of availability period |
| availability_end | TEXT | NOT NULL | End date of availability period |
| type | TEXT | NOT NULL CHECK(type IN ('Room', 'Flat', 'Mini hall')) | Types of Reservation
| beds | INTEGER | NOT NULL, CHECK(beds > 0) | Number of beds available |
| bedrooms | INTEGER | NOT NULL, CHECK(bedrooms > 0) | Number of bedrooms |
| price | REAL | NOT NULL, CHECK(price > 0) | Rental price |
| address | TEXT | NOT NULL | Physical address |
| latitude | REAL | | Latitude coordinate for location |
| longitude | REAL | | Longitude coordinate for location |
| geo_address | TEXT | | Standardized address from DATA.GOV.HK |
| is_reserved | INTEGER | NOT NULL, DEFAULT 0, CHECK(is_reserved IN (0, 1)) | Reservation status (0=available, 1=reserved) |
| average_rating | REAL | DEFAULT 0 | Average of all ratings for this accommodation |
| rating_count | INTEGER | DEFAULT 0 | Number of ratings for this accommodation |

#### Reservation
Manages bookings of accommodations by students.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| reservation_id | INTEGER | PRIMARY KEY | Unique identifier |
| user_id | INTEGER | NOT NULL, FOREIGN KEY | Reference to the User making the reservation |
| accommodation_id | INTEGER | NOT NULL, UNIQUE, FOREIGN KEY | Reference to the reserved Accommodation (unique enforces one-to-one) |
| status | TEXT | NOT NULL, CHECK(status IN ('pending', 'confirmed', 'canceled', 'completed')) | Current status of the reservation |

#### Rating
Stores feedback from students about accommodations.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| rating_id | INTEGER | PRIMARY KEY | Unique identifier |
| reservation_id | INTEGER | NOT NULL, UNIQUE, FOREIGN KEY | Reference to the Reservation being rated |
| rating | INTEGER | NOT NULL, CHECK(rating BETWEEN 0 AND 5) | Numerical score (0-5) |
| date | TEXT | NOT NULL | Date the rating was submitted |

#### Campus
Stores HKU campus locations for distance calculations.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| campus_id | INTEGER | PRIMARY KEY | Unique identifier |
| name | TEXT | NOT NULL | Name of the campus |
| latitude | REAL | NOT NULL | Latitude coordinate |
| longitude | REAL | NOT NULL | Longitude coordinate |

### Triggers

1. **update_accommodation_reserved_insert**
   - Activates: AFTER INSERT ON Reservation
   - Action: Sets is_reserved to 1 on the associated Accommodation

2. **update_accommodation_reserved_delete**
   - Activates: AFTER DELETE ON Reservation 
   - Action: Sets is_reserved to 0 on the associated Accommodation

3. **update_accommodation_rating_insert**
   - Activates: AFTER INSERT ON Rating
   - Action: Updates average_rating and rating_count on the associated Accommodation

4. **update_accommodation_rating_delete**
   - Activates: AFTER DELETE ON Rating
   - Action: Updates average_rating and rating_count on the associated Accommodation

## Database Helper Functions

### User Management

#### register_user(name, email, password, role)
Creates a new user in the system.

**Parameters:**
- `name` (string): User's full name
- `email` (string): User's email address (must be unique)
- `password` (string): User's password (should be hashed before storage)
- `role` (string): Either 'Student' or 'Specialist'

**Returns:**
- Integer: user_id of the created user, or None if failed

**Example:**
```python
user_id = register_user("John Doe", "john.doe@example.com", "hashed_password123", "Student")
if user_id:
    print(f"Created user with ID: {user_id}")
```

#### get_accommodation_with_rating(accommodation_id)
Retrieves an accommodation with its rating information.

**Parameters:**
- `accommodation_id` (integer): ID of the accommodation to retrieve

**Returns:**
- Dictionary with accommodation details including average_rating and rating_count

**Example:**
```python
acc_details = get_accommodation_with_rating(5)
if acc_details:
    print(f"Accommodation ID: {acc_details['accommodation_id']}")
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
- Integer: reservation_id of the created reservation, or None if failed

**Features:**
- Checks if accommodation exists
- Verifies accommodation is not already reserved
- Automatically updates accommodation's is_reserved status via trigger

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
- Integer: rating_id of the created rating, or None if failed

**Features:**
- Verifies reservation exists
- Checks that reservation is 'completed' before allowing rating
- Automatically adds current date to the rating
- Automatically updates the accommodation's average_rating and rating_count via trigger

**Example:**
```python
rating_id = add_rating(reservation_id=3, rating=4)
```
