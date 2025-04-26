import sqlite3
import datetime # Needed for add_rating
import os

# Define the database name consistent with the V5 creation script
DB_NAME = 'unihaven_sprint3.db' # Updated DB Name

def get_db_connection():
    """Get a connection to the database with foreign key support enabled."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, DB_NAME)
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database {db_path}: {e}")
        raise

# --- User Registration Functions (Split) ---

def register_student(name, email, password, contact, campus_id): # Added campus_id
    """Register a new student in the system, linked to a campus"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if campus exists
        cursor.execute('SELECT campus_id FROM Campus WHERE campus_id = ?', (campus_id,))
        if cursor.fetchone() is None:
            print(f"Error registering student: Campus ID {campus_id} not found.")
            return None

        cursor.execute('''
        INSERT INTO Student (name, email, password, contact, campus_id) -- Added campus_id
        VALUES (?, ?, ?, ?, ?)
        ''', (name, email, password, contact, campus_id)) # Added campus_id
        user_id = cursor.lastrowid
        conn.commit()
        print(f"Student registered successfully with user_id: {user_id} for campus_id: {campus_id}")
        return user_id
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: Student.email" in str(e):
             print(f"Error registering student: Email '{email}' already exists.")
        elif "FOREIGN KEY constraint failed" in str(e):
             # This case should be caught by the explicit check above, but kept as fallback
             print(f"Error registering student: Campus ID {campus_id} is invalid (FK constraint).")
        else:
             print(f"Error registering student: {e}")
        return None
    except sqlite3.Error as e:
        print(f"Database error registering student: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def register_specialist(name, email, password, contact, campus_id): # Added campus_id
    """Register a new specialist in the system, linked to a campus"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
         # Check if campus exists
        cursor.execute('SELECT campus_id FROM Campus WHERE campus_id = ?', (campus_id,))
        if cursor.fetchone() is None:
            print(f"Error registering specialist: Campus ID {campus_id} not found.")
            return None

        cursor.execute('''
        INSERT INTO Specialist (name, email, password, contact, campus_id) -- Added campus_id
        VALUES (?, ?, ?, ?, ?)
        ''', (name, email, password, contact, campus_id)) # Added campus_id
        specialist_id = cursor.lastrowid
        conn.commit()
        print(f"Specialist registered successfully with specialist_id: {specialist_id} for campus_id: {campus_id}")
        return specialist_id
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: Specialist.email" in str(e):
             print(f"Error registering specialist: Email '{email}' already exists.")
        elif "FOREIGN KEY constraint failed" in str(e):
             # This case should be caught by the explicit check above, but kept as fallback
             print(f"Error registering specialist: Campus ID {campus_id} is invalid (FK constraint).")
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
                     owner_name, owner_contact, # No change here
                     # --- V5 Schema Specific Fields ---
                     geo_address, # Kept from schema
                     flat_number, # Added
                     floor_number, # Added
                     room_number=None # Added (optional)
                     # specialist_id is REMOVED
                     ):
    """Add a new accommodation listing aligned with the V5 schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO Accommodation (
            availability_start, availability_end, type, beds, bedrooms, price,
            building_name, latitude, longitude, address, geo_address,
            owner_name, owner_contact, is_reserved, average_rating, rating_count,
            room_number, flat_number, floor_number -- Added new fields
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?) -- Added placeholders
        ''', (availability_start, availability_end, type, beds, bedrooms, price,
              building_name, latitude, longitude, address, geo_address,
              owner_name, owner_contact,
              room_number, flat_number, floor_number)) # Added values
        accommodation_id = cursor.lastrowid
        conn.commit()
        print(f"Accommodation added successfully with accommodation_id: {accommodation_id}")
        return accommodation_id
    except sqlite3.IntegrityError as e:
        # Check for the new unique constraint violation
        if "UNIQUE constraint failed: Accommodation.room_number, Accommodation.flat_number, Accommodation.floor_number, Accommodation.geo_address" in str(e):
            print(f"Error adding accommodation: An accommodation with the same room/flat/floor/geo_address already exists.")
        else:
            print(f"Error adding accommodation (IntegrityError): {e}")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding accommodation: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- New Function for Accommodation Offering (Required by V5 Schema) ---
def add_accommodation_offering(accommodation_id, campus_id, specialist_id):
    """Create a link between an accommodation, campus, and specialist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check foreign keys exist before inserting
        cursor.execute('SELECT accommodation_id FROM Accommodation WHERE accommodation_id = ?', (accommodation_id,))
        if not cursor.fetchone():
            print(f"Error adding offering: Accommodation ID {accommodation_id} not found.")
            return None
        cursor.execute('SELECT campus_id FROM Campus WHERE campus_id = ?', (campus_id,))
        if not cursor.fetchone():
            print(f"Error adding offering: Campus ID {campus_id} not found.")
            return None
        cursor.execute('SELECT specialist_id FROM Specialist WHERE specialist_id = ?', (specialist_id,))
        if not cursor.fetchone():
            print(f"Error adding offering: Specialist ID {specialist_id} not found.")
            return None

        cursor.execute('''
        INSERT INTO AccommodationOffering (accommodation_id, campus_id, specialist_id)
        VALUES (?, ?, ?)
        ''', (accommodation_id, campus_id, specialist_id))
        offering_id = cursor.lastrowid
        conn.commit()
        print(f"AccommodationOffering created successfully with offering_id: {offering_id} (Acc:{accommodation_id}, Camp:{campus_id}, Spec:{specialist_id})")
        return offering_id
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: AccommodationOffering.accommodation_id, AccommodationOffering.campus_id" in str(e):
            print(f"Error adding offering: Offering for Accommodation {accommodation_id} at Campus {campus_id} already exists.")
        elif "FOREIGN KEY constraint failed" in str(e):
             print(f"Error adding offering: One of the IDs ({accommodation_id}, {campus_id}, {specialist_id}) is invalid (FK constraint).")
        else:
            print(f"Error adding offering (IntegrityError): {e}")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding offering: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# --- Campus Function (No change needed in logic) ---

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

# --- Reservation Functions (No change needed in logic, but verify FKs) ---

def make_reservation(user_id, accommodation_id, status='pending'):
    """Create a new reservation for a Student"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if the accommodation exists AND is not reserved
        cursor.execute('SELECT is_reserved FROM Accommodation WHERE accommodation_id = ?', (accommodation_id,))
        result = cursor.fetchone()
        if result is None:
            print(f"Error creating reservation: Accommodation ID {accommodation_id} not found.")
            return None
        if result['is_reserved'] == 1: # Access by column name due to row_factory
            print(f"Error creating reservation: Accommodation ID {accommodation_id} is currently reserved.")
            return None

        # Check if the user (student) exists
        cursor.execute('SELECT student_id FROM Student WHERE student_id = ?', (user_id,)) # Check against student_id
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
        # The insert trigger should automatically set is_reserved = 1
        print(f"Reservation created successfully with reservation_id: {reservation_id}")
        return reservation_id
    except sqlite3.IntegrityError as e:
         # This could still happen e.g. FK constraint if student/accommodation deleted mid-process
         print(f"Error creating reservation (IntegrityError): {e}")
         return None
    except sqlite3.Error as e:
        print(f"Database error creating reservation: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def update_reservation_status(reservation_id, status):
    """Update reservation status"""
    allowed_statuses = ('pending', 'confirmed', 'canceled', 'completed')
    if status not in allowed_statuses:
        print(f"Error updating reservation: Invalid status '{status}'. Must be one of {allowed_statuses}.")
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Fetch reservation details needed for potential cancellation logic
        cursor.execute('SELECT reservation_id, accommodation_id, status FROM Reservation WHERE reservation_id = ?', (reservation_id,))
        reservation = cursor.fetchone()
        if reservation is None:
            print(f"Error updating reservation: Reservation ID {reservation_id} not found.")
            return False

        current_status = reservation['status']
        accommodation_id = reservation['accommodation_id']

        # --- Handle Cancellation ---
        # If changing *to* 'canceled', we need to potentially delete the reservation
        # to trigger the is_reserved update (as per V2 logic).
        # Alternatively, modify the trigger or add manual update logic here.
        # Let's stick to the V2 implied logic: cancellation means deletion.
        if status == 'canceled' and current_status != 'canceled':
            cursor.execute('DELETE FROM Reservation WHERE reservation_id = ?', (reservation_id,))
            conn.commit()
            # The DELETE trigger should handle setting is_reserved back to 0 if no other reservations exist.
            print(f"Reservation {reservation_id} status set to 'canceled' (row deleted).")
            return True
        # If changing *from* 'canceled' (i.e., undeleting), this logic doesn't support it easily.
        elif current_status == 'canceled' and status != 'canceled':
             print(f"Error updating reservation: Cannot change status from 'canceled' as the reservation row is typically deleted.")
             return False
        # --- Handle Other Status Updates ---
        elif status != current_status:
            cursor.execute('''
            UPDATE Reservation SET status = ? WHERE reservation_id = ?
            ''', (status, reservation_id))
            conn.commit()
            print(f"Reservation {reservation_id} status updated to '{status}'.")
            # If changing to 'confirmed', the 'is_reserved' flag should already be 1 from the INSERT trigger.
            # No explicit change needed here for is_reserved based on triggers.
            return True
        else:
            print(f"Reservation {reservation_id} status is already '{status}'. No update needed.")
            return True # Indicate success as status is already correct

    except sqlite3.Error as e:
        print(f"Error updating reservation {reservation_id}: {e}")
        conn.rollback() # Rollback in case of error during update/delete
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- Rating Function (No change needed in logic, but verify FKs) ---

def add_rating(user_id, accommodation_id, rating, comment=None):
    """Add a rating given by a Student for an Accommodation"""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not (0 <= rating <= 5):
        print(f"Error adding rating: Rating value {rating} must be between 0 and 5.")
        return None

    try:
        # Check if Student exists
        cursor.execute('SELECT student_id FROM Student WHERE student_id = ?', (user_id,)) # Check student_id
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
        # The insert trigger for Rating should update Accommodation's average_rating and rating_count
        print(f"Rating added successfully with rating_id: {rating_id}")
        return rating_id
    except sqlite3.IntegrityError as e:
        print(f"Error adding rating (IntegrityError): {e}")
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
    # conn.row_factory is already set in get_db_connection
    cursor = conn.cursor()
    try:
        # Select all columns from Accommodation as the schema changed
        cursor.execute('''
        SELECT * FROM Accommodation WHERE accommodation_id = ?
        ''', (accommodation_id,))
        result = cursor.fetchone()
        if result:
            return dict(result) # Convert Row object to a standard dictionary
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
    """Get database statistics based on the V5 schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    stats = {}
    try:
        cursor.execute("SELECT COUNT(*) FROM Campus") # Added Campus count
        stats['campuses'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Student")
        stats['students'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Specialist")
        stats['specialists'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Accommodation")
        stats['accommodations'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM AccommodationOffering") # Added Offering count
        stats['accommodation_offerings'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Accommodation WHERE is_reserved=1")
        stats['reserved_accommodations'] = cursor.fetchone()[0]

        # Count non-canceled reservations (as canceled ones might be deleted)
        cursor.execute("SELECT COUNT(*) FROM Reservation WHERE status != 'canceled'")
        stats['active_reservations'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Rating")
        stats['ratings'] = cursor.fetchone()[0]

        return stats
    except sqlite3.Error as e:
        print(f"Error getting database stats: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- Example Usage (Optional - Updated for V3) ---
if __name__ == '__main__':
    print(f"Running example usage of dbutilsV3 for database '{DB_NAME}'...")

    # --- Prerequisites: Assumes create_dbV5.py has been run ---
    # 1. Add Campuses first
    print("\n--- Adding Campuses ---")
    campus1_id = add_campus("Test Campus 1", 22.1, 114.1)
    campus2_id = add_campus("Test Campus 2", 22.2, 114.2)
    if not campus1_id or not campus2_id:
        print("ERROR: Could not add campuses. Aborting example.")
        exit()

    # 2. Register Users (linked to campuses)
    print("\n--- Registering Users ---")
    student_id = register_student("Alice V3", "alice.v3@example.com", "pass123", "111", campus1_id)
    spec_id = register_specialist("Bob V3", "bob.v3@example.com", "pass456", "999", campus2_id)
    # Test unique email constraint
    spec_id_fail = register_specialist("Bob V3 Again", "bob.v3@example.com", "pass789", "998", campus1_id)
    # Test invalid campus FK
    student_id_fail = register_student("Charlie V3", "charlie.v3@example.com", "pass111", "222", 9999)

    if not student_id or not spec_id:
        print("ERROR: Could not register required student/specialist. Aborting further examples.")
        exit()

    # 3. Add Accommodation (No specialist link here)
    print("\n--- Adding Accommodation ---")
    acc_id = add_accommodation(
        availability_start="2025-09-01", availability_end="2026-06-30",
        type="Flat", beds=2, bedrooms=1, price=1250.75,
        building_name="Future Tower", latitude=22.15, longitude=114.15,
        address="1 Tech Road", owner_name="Prop Co", owner_contact="sales@prop.co",
        geo_address="geo:22.15,114.15", flat_number="10A", floor_number="10", room_number=None
    )
    # Test unique address constraint
    acc_id_fail = add_accommodation(
        availability_start="2025-10-01", availability_end="2026-07-31",
        type="Room", beds=1, bedrooms=1, price=800.00,
        building_name="Future Tower", latitude=22.15, longitude=114.15, # Same location data
        address="1 Tech Road", owner_name="Prop Co", owner_contact="sales@prop.co",
        geo_address="geo:22.15,114.15", flat_number="10A", floor_number="10", room_number=None # Same address details
    )


    if not acc_id:
        print("ERROR: Could not add accommodation. Aborting further examples.")
        exit()

    # 4. Add Accommodation Offering (Link accommodation, campus, specialist)
    print("\n--- Adding Accommodation Offering ---")
    offering_id = add_accommodation_offering(acc_id, campus2_id, spec_id)
    # Test unique offering constraint
    offering_id_fail = add_accommodation_offering(acc_id, campus2_id, spec_id)
     # Test invalid FKs
    offering_id_fail_acc = add_accommodation_offering(9999, campus2_id, spec_id)
    offering_id_fail_camp = add_accommodation_offering(acc_id, 9999, spec_id)
    offering_id_fail_spec = add_accommodation_offering(acc_id, campus2_id, 9999)

    if not offering_id:
        # Note: Accommodation still exists, but isn't 'offered' by a specialist at a campus
        print("Warning: Could not create accommodation offering link.")


    # 5. Make Reservation
    print("\n--- Making Reservation ---")
    res_id = make_reservation(student_id, acc_id, status='pending')
    if res_id:
        print("Reservation made. Checking accommodation status...")
        acc_details_after_res = get_accommodation_with_rating(acc_id)
        print(f"Accommodation {acc_id} is_reserved: {acc_details_after_res.get('is_reserved') if acc_details_after_res else 'Not Found'}")

        # Try reserving again (should fail)
        res_id_fail = make_reservation(student_id, acc_id)

        # 6. Update Reservation Status
        print("\n--- Updating Reservation Status ---")
        update_reservation_status(res_id, 'confirmed')
        update_reservation_status(res_id, 'completed')

        # 7. Add Rating
        print("\n--- Adding Ratings ---")
        rating_id1 = add_rating(student_id, acc_id, 5, "Fantastic V3 place!")
        rating_id2 = add_rating(student_id, acc_id, 4, "Good value V3.")

        # Check rating effects
        acc_details_after_rating = get_accommodation_with_rating(acc_id)
        if acc_details_after_rating:
            print(f"Accommodation {acc_id} average_rating: {acc_details_after_rating.get('average_rating'):.2f}")
            print(f"Accommodation {acc_id} rating_count: {acc_details_after_rating.get('rating_count')}")

        # 8. Cancel Reservation (Simulates student cancelling)
        print("\n--- Cancelling Reservation ---")
        update_reservation_status(res_id, 'canceled') # This should delete the reservation row
        acc_details_after_cancel = get_accommodation_with_rating(acc_id)
        print(f"Accommodation {acc_id} is_reserved after cancel: {acc_details_after_cancel.get('is_reserved') if acc_details_after_cancel else 'Not Found'}")

        # Verify reservation is gone (or status is 'canceled' if logic changed)
        conn_check = get_db_connection()
        cursor_check = conn_check.cursor()
        cursor_check.execute("SELECT * FROM Reservation WHERE reservation_id = ?", (res_id,))
        res_check = cursor_check.fetchone()
        print(f"Reservation {res_id} exists after cancel: {res_check is not None}")
        cursor_check.close()
        conn_check.close()


    # 9. Get Stats
    print("\n--- Getting Final Stats ---")
    stats = get_stats()
    if stats:
        print("Database Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    print("\n--- DB Utils V3 Example Usage Complete ---")
