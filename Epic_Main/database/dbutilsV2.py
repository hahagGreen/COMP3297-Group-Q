import sqlite3
import datetime


def register_user(name, email, password, role, phone=None):
    """Register a new user in the system"""
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO User (name, email, password, role, phone) 
        VALUES (?, ?, ?, ?, ?)
        ''', (name, email, password, role, phone))
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError as e:
        print(f"Error registering user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def add_owner(name, phone):
    """Add a new owner to the system"""
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO Owner (name, phone) 
        VALUES (?, ?)
        ''', (name, phone))
        owner_id = cursor.lastrowid
        conn.commit()
        return owner_id
    except sqlite3.IntegrityError as e:
        print(f"Error adding owner: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def add_building(name, latitude, longitude, address):
    """Add a new building to the system"""
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO Building (name, latitude, longitude, address) 
        VALUES (?, ?, ?, ?)
        ''', (name, latitude, longitude, address))
        building_id = cursor.lastrowid
        conn.commit()
        return building_id
    except sqlite3.IntegrityError as e:
        print(f"Error adding building: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def add_accommodation(availability_start, availability_end, type, beds, bedrooms,
                      price, building_id, owner_id):
    """Add a new accommodation listing"""
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO Accommodation (availability_start, availability_end, type, beds, 
                                  bedrooms, price, building_id, owner_id, 
                                  is_reserved, average_rating, rating_count) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0)
        ''', (availability_start, availability_end, type, beds, bedrooms,
              price, building_id, owner_id))
        accommodation_id = cursor.lastrowid
        conn.commit()
        return accommodation_id
    except sqlite3.IntegrityError as e:
        print(f"Error adding accommodation: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def add_campus(name, latitude, longitude):
    """Add a new campus location"""
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO Campus (name, latitude, longitude) 
        VALUES (?, ?, ?)
        ''', (name, latitude, longitude))
        campus_id = cursor.lastrowid
        conn.commit()
        return campus_id
    except sqlite3.IntegrityError as e:
        print(f"Error adding campus: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def make_reservation(user_id, accommodation_id, status='pending'):
    """Create a new reservation"""
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()

    try:
        # Check if the accommodation is already reserved
        cursor.execute('SELECT is_reserved FROM Accommodation WHERE accommodation_id = ?', (accommodation_id,))
        result = cursor.fetchone()

        if result is None:
            print(f"Error: Accommodation {accommodation_id} not found")
            return None

        if result[0] == 1:
            print(f"Error: Accommodation {accommodation_id} is already reserved")
            return None

        # Create the reservation
        cursor.execute('''
        INSERT INTO Reservation (user_id, accommodation_id, status) 
        VALUES (?, ?, ?)
        ''', (user_id, accommodation_id, status))
        reservation_id = cursor.lastrowid
        conn.commit()
        return reservation_id
    except sqlite3.IntegrityError as e:
        print(f"Error creating reservation: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def update_reservation_status(reservation_id, status):
    """Update reservation status"""
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
        UPDATE Reservation SET status = ? WHERE reservation_id = ?
        ''', (status, reservation_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating reservation: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def add_rating(reservation_id, rating):
    """Add a rating for a completed reservation"""
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()

    today = datetime.datetime.now().strftime("%Y-%m-%d")

    try:
        # Check if the reservation exists and is completed
        cursor.execute('SELECT status FROM Reservation WHERE reservation_id = ?', (reservation_id,))
        result = cursor.fetchone()

        if result is None:
            print(f"Error: Reservation {reservation_id} not found")
            return None

        if result[0] != 'completed':
            print(f"Error: Reservation {reservation_id} is not completed")
            return None

        # Add the rating
        cursor.execute('''
        INSERT INTO Rating (reservation_id, rating, date) 
        VALUES (?, ?, ?)
        ''', (reservation_id, rating, today))
        rating_id = cursor.lastrowid
        conn.commit()
        return rating_id
    except sqlite3.IntegrityError as e:
        print(f"Error adding rating: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_accommodation_with_rating(accommodation_id):
    """Get accommodation details with its rating information and building details"""
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT a.*, b.name as building_name, b.address, b.latitude, b.longitude 
        FROM Accommodation a
        JOIN Building b ON a.building_id = b.building_id
        WHERE a.accommodation_id = ?
        ''', (accommodation_id,))

        result = cursor.fetchone()
        if result:
            # Convert to dictionary for easier access
            columns = [desc[0] for desc in cursor.description]
            accommodation = dict(zip(columns, result))
            return accommodation
        return None
    except sqlite3.Error as e:
        print(f"Error retrieving accommodation: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_stats():
    """Get database statistics"""
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()

    stats = {}

    try:
        cursor.execute("SELECT COUNT(*) FROM User WHERE role='Student'")
        stats['students'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM User WHERE role='Specialist'")
        stats['specialists'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Owner")
        stats['owners'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Building")
        stats['buildings'] = cursor.fetchone()[0]

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
        print(f"Error getting stats: {e}")
        return None
    finally:
        cursor.close()
        conn.close()