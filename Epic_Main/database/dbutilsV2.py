import sqlite3
import datetime

def register_user(name, email, password, role, phone=None):
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

def add_building(name, latitude, longitude, address, geo_address=None):
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO Building (name, latitude, longitude, address, geo_address)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, latitude, longitude, address, geo_address))
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
                      price, building_id, owner_id, unit=None):
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO Accommodation (availability_start, availability_end, type, beds,
                                  bedrooms, price, building_id, owner_id, unit,
                                  is_reserved, average_rating, rating_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0)
        ''', (availability_start, availability_end, type, beds, bedrooms,
              price, building_id, owner_id, unit))
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
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT is_reserved FROM Accommodation WHERE accommodation_id = ?', (accommodation_id,))
        result = cursor.fetchone()
        if result is None or result[0] == 1:
            print(f"Error: Accommodation {accommodation_id} unavailable")
            return None
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

def add_rating(reservation_id, rating, comment=None):
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        cursor.execute('SELECT status FROM Reservation WHERE reservation_id = ?', (reservation_id,))
        result = cursor.fetchone()
        if result is None or result[0] != 'completed':
            print(f"Error: Reservation {reservation_id} invalid for rating")
            return None
        cursor.execute('''
        INSERT INTO Rating (reservation_id, rating, comment, date)
        VALUES (?, ?, ?, ?)
        ''', (reservation_id, rating, comment, today))
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
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT a.*, b.name AS building_name, b.address, b.latitude, b.longitude, b.geo_address
        FROM Accommodation a
        JOIN Building b ON a.building_id = b.building_id
        WHERE a.accommodation_id = ?
        ''', (accommodation_id,))
        result = cursor.fetchone()
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        return None
    except sqlite3.Error as e:
        print(f"Error retrieving accommodation: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_stats():
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()
    stats = {}
    try:
        for key, query in [
            ('students', "SELECT COUNT(*) FROM User WHERE role='Student'"),
            ('specialists', "SELECT COUNT(*) FROM User WHERE role='Specialist'"),
            ('owners', "SELECT COUNT(*) FROM Owner"),
            ('buildings', "SELECT COUNT(*) FROM Building"),
            ('accommodations', "SELECT COUNT(*) FROM Accommodation"),
            ('reserved_accommodations', "SELECT COUNT(*) FROM Accommodation WHERE is_reserved=1"),
            ('reservations', "SELECT COUNT(*) FROM Reservation"),
            ('ratings', "SELECT COUNT(*) FROM Rating")
        ]:
            cursor.execute(query)
            stats[key] = cursor.fetchone()[0]
        return stats
    except sqlite3.Error as e:
        print(f"Error getting stats: {e}")
        return None
    finally:
        cursor.close()
        conn.close()