import sqlite3
# import datetime # Not used in this version
import os

def create_database():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the database file
    db_path = os.path.join(script_dir, 'unihaven.db') # Use a new db name

    # Delete existing database file if it exists to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")

    # Connect to the database using the full path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON;")

    # --- Create Tables based on Domain Model ---

    # Create Student table (previously User)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Student (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        contact TEXT  -- Added contact as per model
    )
    ''')

    # Create Specialist table (new table as per model)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Specialist (
        specialist_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        contact TEXT NOT NULL -- Added contact as per model
    )
    ''')

    # Create Accommodation table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Accommodation (
        accommodation_id INTEGER PRIMARY KEY,
        specialist_id INTEGER, -- Added FK to Specialist
        availability_start TEXT NOT NULL,
        availability_end TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('Room', 'Flat', 'Mini hall')),
        beds INTEGER NOT NULL CHECK(beds > 0),
        bedrooms INTEGER NOT NULL CHECK(bedrooms > 0),
        price REAL NOT NULL CHECK(price > 0),
        building_name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        address TEXT NOT NULL,
        geo_address TEXT, -- Kept geo_address
        owner_name TEXT NOT NULL,
        owner_contact TEXT NOT NULL, -- Changed owner_phone to owner_contact
        -- unit TEXT, -- Removed unit as it wasn't in the model diagram
        is_reserved INTEGER NOT NULL DEFAULT 0 CHECK(is_reserved IN (0, 1)), -- Kept SQLite boolean style
        average_rating REAL DEFAULT 0, -- Kept rating fields
        rating_count INTEGER DEFAULT 0, -- Kept rating fields
        FOREIGN KEY (specialist_id) REFERENCES Specialist(specialist_id) ON DELETE SET NULL -- Added FK constraint
    )
    ''')

    # Create Reservation table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Reservation (
        reservation_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL, -- FK to Student
        accommodation_id INTEGER NOT NULL, -- Removed UNIQUE constraint here
        status TEXT NOT NULL CHECK(status IN ('pending', 'confirmed', 'canceled', 'completed')),
        FOREIGN KEY (user_id) REFERENCES Student(user_id) ON DELETE CASCADE, -- Points to Student table now
        FOREIGN KEY (accommodation_id) REFERENCES Accommodation(accommodation_id) ON DELETE CASCADE
    )
    ''')

    # Create Rating table (linked to Student and Accommodation directly)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Rating (
        rating_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL, -- FK to Student
        accommodation_id INTEGER NOT NULL, -- FK to Accommodation
        rating INTEGER NOT NULL CHECK(rating BETWEEN 0 AND 5),
        comment TEXT,
        date TEXT NOT NULL, -- Kept TEXT for simplicity in SQLite
        FOREIGN KEY (user_id) REFERENCES Student(user_id) ON DELETE CASCADE, -- Points to Student
        FOREIGN KEY (accommodation_id) REFERENCES Accommodation(accommodation_id) ON DELETE CASCADE -- Points to Accommodation
        -- Removed UNIQUE constraint on reservation_id as it's gone
        -- Could add UNIQUE(user_id, accommodation_id, date) if needed, but model doesn't specify
    )
    ''')

    # Create Campus table (remains largely the same)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Campus (
        campus_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL
    )
    ''')

    # --- Create Triggers (Adapting Rating Triggers) ---

    # Triggers to update Accommodation.is_reserved based on Reservation changes (remain the same)
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
        -- Only set to 0 if there are no other reservations for this accommodation
        UPDATE Accommodation SET is_reserved = 0
        WHERE accommodation_id = OLD.accommodation_id
          AND NOT EXISTS (SELECT 1 FROM Reservation WHERE accommodation_id = OLD.accommodation_id);
    END;
    ''') # Adjusted delete trigger logic slightly for non-unique reservations


    # Triggers to update Accommodation rating based on Rating changes (modified for direct links)
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_accommodation_rating_insert
    AFTER INSERT ON Rating
    BEGIN
        UPDATE Accommodation
        SET
            rating_count = rating_count + 1,
            -- Ensure division by zero doesn't happen, though rating_count starts at 0
            -- The initial state average_rating * rating_count = 0 * 0 = 0
            -- First rating: (0 + NEW.rating) / (0 + 1) = NEW.rating
            -- Subsequent: (current_avg * old_count + NEW.rating) / (old_count + 1)
            average_rating = ( (average_rating * rating_count) + NEW.rating ) / ( rating_count + 1.0 ) -- use 1.0 for float division
        WHERE
            accommodation_id = NEW.accommodation_id; -- Use direct accommodation_id from Rating
    END;
    ''')

    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_accommodation_rating_delete
    AFTER DELETE ON Rating
    BEGIN
        UPDATE Accommodation
        SET
            -- average_rating calculation needs care when removing a rating
            average_rating = CASE
                WHEN rating_count <= 1 THEN 0 -- If this was the last rating, reset avg to 0
                ELSE ( (average_rating * rating_count) - OLD.rating ) / ( rating_count - 1.0 ) -- Subtract rating and decrement count
            END,
             rating_count = rating_count - 1 -- Decrement count last
        WHERE
            accommodation_id = OLD.accommodation_id; -- Use direct accommodation_id from Rating
    END;
    ''')


    # Commit changes
    conn.commit()

    # Check if tables are created
    print("\n--- Checking Database Schema ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:", tables)

    # Check triggers
    cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger';")
    triggers = cursor.fetchall()
    print("Triggers in the database:", triggers)

    # Example: Check columns and FKs for a specific table (optional)
    print("\nColumns in Accommodation table:")
    cursor.execute("PRAGMA table_info(Accommodation);")
    print(cursor.fetchall())
    print("\nForeign Keys for Accommodation table:")
    cursor.execute("PRAGMA foreign_key_list(Accommodation);")
    print(cursor.fetchall())

    print("\nColumns in Rating table:")
    cursor.execute("PRAGMA table_info(Rating);")
    print(cursor.fetchall())
    print("\nForeign Keys for Rating table:")
    cursor.execute("PRAGMA foreign_key_list(Rating);")
    print(cursor.fetchall())


    # Close connection
    cursor.close()
    conn.close()
    print("\n--- Database Creation Complete ---")

if __name__ == "__main__":
    create_database()
    print("\nDatabase created reflecting the domain model structure.")