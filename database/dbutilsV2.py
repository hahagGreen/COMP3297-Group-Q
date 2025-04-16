import sqlite3
import datetime # Needed for add_rating
import os

# Define the database name consistent with the creation script
DB_NAME = 'unihaven.db'

def get_db_connection():
    """Get a connection to the database with foreign key support enabled."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, DB_NAME)
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database {db_path}: {e}")
        # Consider raising the exception or returning None depending on desired error handling
        raise

# --- User Registration Functions (Split) ---

def register_student(name, email, password, contact):
    """Register a new student in the system"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO Student (name, email, password, contact)
        VALUES (?, ?, ?, ?)
        ''', (name, email, password, contact))
        user_id = cursor.lastrowid
        conn.commit()
        print(f"Student registered successfully with user_id: {user_id}")
        return user_id
    except sqlite3.IntegrityError as e:
        # Specific check for unique email constraint
        if "UNIQUE constraint failed: Student.email" in str(e):
             print(f"Error registering student: Email '{email}' already exists.")
        else:
             print(f"Error registering student: {e}")
        return None
    except sqlite3.Error as e:
        print(f"Database error registering student: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def register_specialist(name, email, password, contact):
    """Register a new specialist in the system"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO Specialist (name, email, password, contact)
        VALUES (?, ?, ?, ?)
        ''', (name, email, password, contact))
        specialist_id = cursor.lastrowid
        conn.commit()
        print(f"Specialist registered successfully with specialist_id: {specialist_id}")
        return specialist_id
    except sqlite3.IntegrityError as e:
         # Specific check for unique email constraint
        if "UNIQUE constraint failed: Specialist.email" in str(e):
             print(f"Error registering specialist: Email '{email}' already exists.")
        else:
             print(f"Error registering specialist: {e}")
        return None
    except sqlite3.Error as e:
        print(f"Database error registering specialist: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- Accommodation Function ---

def add_accommodation(availability_start, availability_end, type, beds, bedrooms,
                     price, building_name, latitude, longitude, address,
                     owner_name, owner_contact, # Changed from owner_phone
                     specialist_id=None, # Added optional specialist_id
                     geo_address=None):
    """Add a new accommodation listing aligned with the new schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO Accommodation (
            specialist_id, availability_start, availability_end, type, beds, bedrooms, price,
            building_name, latitude, longitude, address, geo_address,
            owner_name, owner_contact, is_reserved, average_rating, rating_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0)
        ''', (specialist_id, availability_start, availability_end, type, beds, bedrooms, price,
              building_name, latitude, longitude, address, geo_address,
              owner_name, owner_contact)) # Using owner_contact
        accommodation_id = cursor.lastrowid
        conn.commit()
        print(f"Accommodation added successfully with accommodation_id: {accommodation_id}")
        return accommodation_id
    except sqlite3.IntegrityError as e:
        # Check if it's a foreign key constraint failure
        if "FOREIGN KEY constraint failed" in str(e) and specialist_id is not None:
            print(f"Error adding accommodation: Specialist with ID {specialist_id} does not exist.")
        else:
            print(f"Error adding accommodation: {e}")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding accommodation: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- Campus Function ---

def add_campus(name, latitude, longitude):
    """Add a new campus location"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO Campus (name, latitude, longitude)
        VALUES (?, ?, ?)
        ''', (name, latitude, longitude))
        campus_id = cursor.lastrowid
        conn.commit()
        print(f"Campus added successfully with campus_id: {campus_id}")
        return campus_id
    except sqlite3.IntegrityError as e:
        print(f"Error adding campus: {e}") # Could be unique constraint if name is unique
        return None
    except sqlite3.Error as e:
        print(f"Database error adding campus: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- Reservation Functions ---

def make_reservation(user_id, accommodation_id, status='pending'):
    """Create a new reservation for a Student"""
    # Note: user_id now refers to Student.user_id
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if the accommodation exists
        cursor.execute('SELECT is_reserved FROM Accommodation WHERE accommodation_id = ?', (accommodation_id,))
        result = cursor.fetchone()
        if result is None:
            print(f"Error creating reservation: Accommodation ID {accommodation_id} not found.")
            return None

        # Check if the accommodation is currently marked as reserved by the trigger system
        # This simple check assumes the is_reserved flag correctly indicates current availability
        if result[0] == 1:
            print(f"Error creating reservation: Accommodation ID {accommodation_id} is currently reserved.")
            return None

        # Check if the user (student) exists
        cursor.execute('SELECT user_id FROM Student WHERE user_id = ?', (user_id,))
        if cursor.fetchone() is None:
             print(f"Error creating reservation: Student ID {user_id} not found.")
             return None

        # Create the reservation
        cursor.execute('''
        INSERT INTO Reservation (user_id, accommodation_id, status)
        VALUES (?, ?, ?)
        ''', (user_id, accommodation_id, status))
        reservation_id = cursor.lastrowid
        conn.commit()
        print(f"Reservation created successfully with reservation_id: {reservation_id}")
        return reservation_id
    except sqlite3.IntegrityError as e:
        # This could still happen e.g. FK constraint if student/accommodation deleted mid-process
         print(f"Error creating reservation: {e}")
         return None
    except sqlite3.Error as e:
        print(f"Database error creating reservation: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def update_reservation_status(reservation_id, status):
    """Update reservation status"""
    # Ensure status is one of the allowed values
    allowed_statuses = ('pending', 'confirmed', 'canceled', 'completed')
    if status not in allowed_statuses:
        print(f"Error updating reservation: Invalid status '{status}'. Must be one of {allowed_statuses}.")
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT reservation_id FROM Reservation WHERE reservation_id = ?', (reservation_id,))
        if cursor.fetchone() is None:
            print(f"Error updating reservation: Reservation ID {reservation_id} not found.")
            return False

        cursor.execute('''
        UPDATE Reservation SET status = ? WHERE reservation_id = ?
        ''', (status, reservation_id))
        conn.commit()
        print(f"Reservation {reservation_id} status updated to '{status}'.")
        # Note: Triggers handle is_reserved flag updates if status changes to 'canceled' (via DELETE trigger)
        # If status changes FROM 'canceled' to something else, you might need manual logic or another trigger
        # if the DELETE trigger fires on cancellation. Assuming DELETE trigger only fires on actual row deletion.
        return True
    except sqlite3.Error as e:
        print(f"Error updating reservation {reservation_id}: {e}")
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- Rating Function ---

def add_rating(user_id, accommodation_id, rating, comment=None):
    """Add a rating given by a Student for an Accommodation"""
    # Note: No longer linked directly to a reservation_id or status check within this function
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Using date and time

    # Validate rating value
    if not (0 <= rating <= 5):
        print(f"Error adding rating: Rating value {rating} must be between 0 and 5.")
        return None

    try:
        # Check if Student exists
        cursor.execute('SELECT user_id FROM Student WHERE user_id = ?', (user_id,))
        if cursor.fetchone() is None:
             print(f"Error adding rating: Student ID {user_id} not found.")
             return None

        # Check if Accommodation exists
        cursor.execute('SELECT accommodation_id FROM Accommodation WHERE accommodation_id = ?', (accommodation_id,))
        if cursor.fetchone() is None:
             print(f"Error adding rating: Accommodation ID {accommodation_id} not found.")
             return None

        # Add the rating
        cursor.execute('''
        INSERT INTO Rating (user_id, accommodation_id, rating, comment, date)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, accommodation_id, rating, comment, today))
        rating_id = cursor.lastrowid
        conn.commit()
        print(f"Rating added successfully with rating_id: {rating_id}")
        return rating_id
    except sqlite3.IntegrityError as e:
         # Could be FK constraint if student/accommodation deleted mid-process
        print(f"Error adding rating: {e}")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding rating: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- Retrieval Functions ---

def get_accommodation_with_rating(accommodation_id):
    """Get accommodation details including average rating and count"""
    conn = get_db_connection()
    # Use DictCursor for easier access to results by column name
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT * FROM Accommodation WHERE accommodation_id = ?
        ''', (accommodation_id,))
        result = cursor.fetchone()
        if result:
            # Convert Row object to a standard dictionary
            return dict(result)
        else:
            print(f"Accommodation with ID {accommodation_id} not found.")
            return None
    except sqlite3.Error as e:
        print(f"Error retrieving accommodation {accommodation_id}: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- Statistics Function ---

def get_stats():
    """Get database statistics based on the new schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    stats = {}
    try:
        cursor.execute("SELECT COUNT(*) FROM Student") # Query Student table
        stats['students'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Specialist") # Query Specialist table
        stats['specialists'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Accommodation")
        stats['accommodations'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Accommodation WHERE is_reserved=1")
        stats['reserved_accommodations'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Reservation")
        stats['reservations'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Rating")
        stats['ratings'] = cursor.fetchone()[0]

        return stats
    except sqlite3.Error as e:
        print(f"Error getting database stats: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- Example Usage (Optional) ---
if __name__ == '__main__':
    print("Running example usage of db_utils...")

    # Ensure the database exists first by running the create_database script
    # If not, these operations will fail.

    # Example: Register users
    student_id = register_student("Alice Wonderland", "alice@example.com", "pass123", "111-222-3333")
    spec_id = register_specialist("Bob The Builder", "bob@example.com", "pass456", "999-888-7777")
    spec_id_fail = register_specialist("Bob The Builder Again", "bob@example.com", "pass789", "999-888-7777") # Should fail (email unique)


    if spec_id:
      # Example: Add accommodation managed by Bob
      acc_id = add_accommodation(
          specialist_id=spec_id,
          availability_start="2025-09-01", availability_end="2026-06-30",
          type="Flat", beds=2, bedrooms=1, price=1200.50,
          building_name="Wonder Apartments", latitude=1.3521, longitude=103.8198,
          address="123 Fantasy Lane", owner_name="Property Group A", owner_contact="contact@groupa.com",
          geo_address="geo:1.3521,103.8198"
      )
    else:
        acc_id = None
        print("Skipping accommodation add as specialist registration failed.")

    if student_id and acc_id:
        # Example: Make reservation
        res_id = make_reservation(student_id, acc_id, status='confirmed')
        res_id_fail = make_reservation(student_id, acc_id) # Should fail (already reserved)

        # Example: Add rating (assuming reservation completed later)
        # update_reservation_status(res_id, 'completed') # Simulate completion
        rating_id = add_rating(student_id, acc_id, 5, "Excellent place!")
        rating_id_2 = add_rating(student_id, acc_id, 4, "Good value.") # Add another rating

        # Example: Get accommodation details
        acc_details = get_accommodation_with_rating(acc_id)
        if acc_details:
            print("\nAccommodation Details:")
            for key, value in acc_details.items():
                print(f"  {key}: {value}")

    # Example: Get stats
    stats = get_stats()
    if stats:
        print("\nDatabase Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")