import sqlite3
import os

def create_database():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the database file
    db_path = os.path.join(script_dir, 'unihaven_sprint3.db') # Use a new db name for clarity

    # Delete existing database file if it exists to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")

    # Connect to the database using the full path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON;")

    # --- Create Tables based on Updated Domain Model & Recommendations ---

    # Create Campus table (No changes needed based on recommendations)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Campus (
        campus_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL
    )
    ''')
    print("Created Campus table.")

    # Create Student table (Add campus_id FK)
    # Note: Based on the domain model diagram showing a required (1) link,
    # using NOT NULL instead of the recommended SET NULL. Adjust if needed.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Student (
        student_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        contact TEXT,
        campus_id INTEGER NOT NULL, -- Added campus link
        FOREIGN KEY (campus_id) REFERENCES Campus(campus_id) -- Define FK constraint
          -- ON DELETE SET NULL -- Alternative based on text recommendation if a student can exist without campus temporarily
          ON DELETE RESTRICT -- Or RESTRICT/NO ACTION if a campus shouldn't be deleted if students are linked
    )
    ''')
    print("Created Student table with campus_id.")

    # Create Specialist table (Add campus_id FK)
    # Note: Same rationale as Student for NOT NULL based on diagram.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Specialist (
        specialist_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        contact TEXT NOT NULL,
        campus_id INTEGER NOT NULL, -- Added campus link
        FOREIGN KEY (campus_id) REFERENCES Campus(campus_id) -- Define FK constraint
          -- ON DELETE SET NULL -- Alternative based on text recommendation
          ON DELETE RESTRICT -- Or RESTRICT/NO ACTION
    )
    ''')
    print("Created Specialist table with campus_id.")

    # Create Accommodation table (Remove specialist_id, add address fields & unique constraint)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Accommodation (
        accommodation_id INTEGER PRIMARY KEY,
        -- specialist_id INTEGER, -- REMOVED direct FK to Specialist
        availability_start TEXT NOT NULL, -- Consider using DATE type if appropriate
        availability_end TEXT NOT NULL,   -- Consider using DATE type if appropriate
        type TEXT NOT NULL CHECK(type IN ('Room', 'Flat', 'Mini hall')),
        beds INTEGER NOT NULL CHECK(beds > 0),
        bedrooms INTEGER NOT NULL CHECK(bedrooms > 0),
        price REAL NOT NULL CHECK(price > 0), -- Consider DECIMAL/NUMERIC for currency
        building_name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        address TEXT NOT NULL,
        geo_address TEXT, -- Kept geo_address, part of unique identifier

        -- Added detailed address fields
        room_number TEXT, -- Can be NULL as per recommendation
        flat_number TEXT NOT NULL,
        floor_number TEXT NOT NULL,

        owner_name TEXT NOT NULL,
        owner_contact TEXT NOT NULL,
        is_reserved INTEGER NOT NULL DEFAULT 0 CHECK(is_reserved IN (0, 1)),
        average_rating REAL DEFAULT 0,
        rating_count INTEGER DEFAULT 0,
        -- FOREIGN KEY (specialist_id) REFERENCES Specialist(specialist_id) ON DELETE SET NULL -- REMOVED FK constraint

        -- Added unique constraint for address components
        UNIQUE (room_number, flat_number, floor_number, geo_address)
    )
    ''')
    print("Created Accommodation table with detailed address fields, unique constraint, and removed specialist_id.")


    # Create AccommodationOffering table (New intermediary table)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS AccommodationOffering (
        offering_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Added a simple PK
        accommodation_id INTEGER NOT NULL,
        campus_id INTEGER NOT NULL,
        specialist_id INTEGER NOT NULL,
        FOREIGN KEY (accommodation_id) REFERENCES Accommodation(accommodation_id) ON DELETE CASCADE,
        FOREIGN KEY (campus_id) REFERENCES Campus(campus_id) ON DELETE CASCADE,
        FOREIGN KEY (specialist_id) REFERENCES Specialist(specialist_id) ON DELETE CASCADE,
        UNIQUE (accommodation_id, campus_id) -- Ensures one offering per accommodation per campus
    )
    ''')
    print("Created AccommodationOffering table.")

    # Create Reservation table (No changes needed based on recommendations)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Reservation (
        reservation_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL, -- FK to Student
        accommodation_id INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending', 'confirmed', 'canceled', 'completed')),
        FOREIGN KEY (user_id) REFERENCES Student(user_id) ON DELETE CASCADE,
        FOREIGN KEY (accommodation_id) REFERENCES Accommodation(accommodation_id) ON DELETE CASCADE
    )
    ''')
    print("Created Reservation table.")

    # Create Rating table (No changes needed based on recommendations)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Rating (
        rating_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL, -- FK to Student
        accommodation_id INTEGER NOT NULL, -- FK to Accommodation
        rating INTEGER NOT NULL CHECK(rating BETWEEN 0 AND 5),
        comment TEXT,
        date TEXT NOT NULL, -- Consider using DATETIME type
        FOREIGN KEY (user_id) REFERENCES Student(user_id) ON DELETE CASCADE,
        FOREIGN KEY (accommodation_id) REFERENCES Accommodation(accommodation_id) ON DELETE CASCADE
    )
    ''')
    print("Created Rating table.")

    # --- Create Triggers (Keep existing triggers as they are not affected by these changes) ---
    # Triggers for is_reserved based on Reservation changes
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
        UPDATE Accommodation SET is_reserved = 0
        WHERE accommodation_id = OLD.accommodation_id
          AND NOT EXISTS (SELECT 1 FROM Reservation WHERE accommodation_id = OLD.accommodation_id);
    END;
    ''')

    # Triggers for average_rating based on Rating changes
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_accommodation_rating_insert
    AFTER INSERT ON Rating
    BEGIN
        UPDATE Accommodation
        SET
            rating_count = rating_count + 1,
            average_rating = ( (average_rating * (rating_count -1)) + NEW.rating ) / ( rating_count * 1.0 ) -- Corrected logic: use previous count before increment
        WHERE
            accommodation_id = NEW.accommodation_id;

        -- Recalculate average_rating using the just updated rating_count
        UPDATE Accommodation
        SET average_rating = ( (average_rating * (rating_count -1)) + NEW.rating ) / ( rating_count * 1.0 )
        WHERE accommodation_id = NEW.accommodation_id;

    END;
    ''')

    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_accommodation_rating_delete
    AFTER DELETE ON Rating
    BEGIN
        UPDATE Accommodation
        SET
             average_rating = CASE
                 WHEN rating_count <= 1 THEN 0 -- If this was the last rating, reset avg to 0
                 ELSE ( (average_rating * rating_count) - OLD.rating ) / ( (rating_count - 1) * 1.0 ) -- Subtract rating and decrement count
             END,
              rating_count = rating_count - 1 -- Decrement count *after* using the old count in calculation
        WHERE
            accommodation_id = OLD.accommodation_id;
    END;
    ''')
    print("Created/Verified Triggers.")

    # Commit changes
    conn.commit()

    # --- Verification (Optional but recommended) ---
    print("\n--- Checking Database Schema ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:", [t[0] for t in tables])

    print("\nColumns in Student table:")
    cursor.execute("PRAGMA table_info(Student);")
    print(cursor.fetchall())
    print("\nForeign Keys for Student table:")
    cursor.execute("PRAGMA foreign_key_list(Student);")
    print(cursor.fetchall())

    print("\nColumns in Specialist table:")
    cursor.execute("PRAGMA table_info(Specialist);")
    print(cursor.fetchall())
    print("\nForeign Keys for Specialist table:")
    cursor.execute("PRAGMA foreign_key_list(Specialist);")
    print(cursor.fetchall())

    print("\nColumns in Accommodation table:")
    cursor.execute("PRAGMA table_info(Accommodation);")
    print(cursor.fetchall())
    print("\nForeign Keys for Accommodation table:")
    cursor.execute("PRAGMA foreign_key_list(Accommodation);")
    print(cursor.fetchall())
    print("\nUnique Constraints for Accommodation table:")
    cursor.execute("PRAGMA index_list('Accommodation');")
    # Find the auto-index created for the UNIQUE constraint
    unique_indexes = [idx for idx in cursor.fetchall() if idx[2] == 1 and 'autoindex_Accommodation' in idx[1]] # Check if unique and likely auto-created
    for idx in unique_indexes:
      cursor.execute(f"PRAGMA index_info('{idx[1]}');")
      print(f"Index {idx[1]} on columns: {[col[2] for col in cursor.fetchall()]}")


    print("\nColumns in AccommodationOffering table:")
    cursor.execute("PRAGMA table_info(AccommodationOffering);")
    print(cursor.fetchall())
    print("\nForeign Keys for AccommodationOffering table:")
    cursor.execute("PRAGMA foreign_key_list(AccommodationOffering);")
    print(cursor.fetchall())
    print("\nUnique Constraints for AccommodationOffering table:")
    cursor.execute("PRAGMA index_list('AccommodationOffering');")
    unique_indexes_offering = [idx for idx in cursor.fetchall() if idx[2] == 1 and 'autoindex_AccommodationOffering' in idx[1]]
    for idx in unique_indexes_offering:
       cursor.execute(f"PRAGMA index_info('{idx[1]}');")
       print(f"Index {idx[1]} on columns: {[col[2] for col in cursor.fetchall()]}")


    print("\nTriggers in the database:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger';")
    triggers = cursor.fetchall()
    print([t[0] for t in triggers])

    # Close connection
    cursor.close()
    conn.close()
    print("\n--- Database Creation Complete ---")

if __name__ == "__main__":
    create_database()
    print("\nDatabase created reflecting Sprint 3 requirements and domain model.")
