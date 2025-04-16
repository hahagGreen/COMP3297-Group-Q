import sqlite3
import datetime

def create_database():
    # Connect to the database
    conn = sqlite3.connect('unihavenV2.db')
    cursor = conn.cursor()

    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Create User table with phone field added
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS User (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Student', 'Specialist')),
        phone TEXT
    )
    ''')

    # Create Owner table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Owner (
        owner_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT NOT NULL
    )
    ''')

    # Create Building table with geo_address
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Building (
        building_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        address TEXT NOT NULL,
        geo_address TEXT
    )
    ''')

    # Create Accommodation table with building_id, owner_id, and unit
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Accommodation (
        accommodation_id INTEGER PRIMARY KEY,
        availability_start TEXT NOT NULL,
        availability_end TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('Room', 'Flat', 'Mini hall')),
        beds INTEGER NOT NULL CHECK(beds > 0),
        bedrooms INTEGER NOT NULL CHECK(bedrooms > 0),
        price REAL NOT NULL CHECK(price > 0),
        building_id INTEGER NOT NULL,
        owner_id INTEGER NOT NULL,
        unit TEXT,
        is_reserved INTEGER NOT NULL DEFAULT 0 CHECK(is_reserved IN (0, 1)),
        average_rating REAL DEFAULT 0,
        rating_count INTEGER DEFAULT 0,
        FOREIGN KEY (building_id) REFERENCES Building(building_id) ON DELETE CASCADE,
        FOREIGN KEY (owner_id) REFERENCES Owner(owner_id) ON DELETE CASCADE
    )
    ''')

    # Create Reservation table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Reservation (
        reservation_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        accommodation_id INTEGER NOT NULL UNIQUE,
        status TEXT NOT NULL CHECK(status IN ('pending', 'confirmed', 'canceled', 'completed')),
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
        FOREIGN KEY (accommodation_id) REFERENCES Accommodation(accommodation_id) ON DELETE CASCADE
    )
    ''')

    # Create Rating table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Rating (
        rating_id INTEGER PRIMARY KEY,
        reservation_id INTEGER NOT NULL UNIQUE,
        rating INTEGER NOT NULL CHECK(rating BETWEEN 0 AND 5),
        comment TEXT,
        date TEXT NOT NULL,
        FOREIGN KEY (reservation_id) REFERENCES Reservation(reservation_id) ON DELETE CASCADE
    )
    ''')

    # Create Campus table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Campus (
        campus_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL
    )
    ''')

    # Create triggers to maintain relationships
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_accommodation_reserved_insert
    AFTER INSERT ON Reservation
    BEGIN
        UPDATE Accommodation SET is_reserved = 1 WHERE accommodation_id = NEW.accommodation_id;
    END;
    ''')

    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_accommodation_reserved_delete
    AFTER DELETE ON Reservation
    BEGIN
        UPDATE Accommodation SET is_reserved = 0 WHERE accommodation_id = OLD.accommodation_id;
    END;
    ''')

    # Fixed trigger to correctly reference NEW.rating
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_accommodation_rating_insert
    AFTER INSERT ON Rating
    BEGIN
        UPDATE Accommodation 
        SET 
            rating_count = rating_count + 1,
            average_rating = (average_rating * rating_count + NEW.rating) / (rating_count + 1)
        WHERE 
            accommodation_id = (SELECT accommodation_id FROM Reservation WHERE reservation_id = NEW.reservation_id);
    END;
    ''')

    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_accommodation_rating_delete
    AFTER DELETE ON Rating
    BEGIN
        UPDATE Accommodation 
        SET 
            rating_count = rating_count - 1,
            average_rating = CASE
                WHEN rating_count <= 1 THEN 0
                ELSE (average_rating * (rating_count + 1) - OLD.rating) / (rating_count)
            END
        WHERE 
            accommodation_id = (SELECT accommodation_id FROM Reservation WHERE reservation_id = OLD.reservation_id);
    END;
    ''')

    # Commit changes
    conn.commit()

    # Check if tables are created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:", tables)

    # Check triggers
    cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger';")
    triggers = cursor.fetchall()
    print("Triggers in the database:", triggers)

    # Close connection
    cursor.close()
    conn.close()

if __name__ == "__main__":
    create_database()
    print("\nDatabase created with all tables, constraints, and triggers.")