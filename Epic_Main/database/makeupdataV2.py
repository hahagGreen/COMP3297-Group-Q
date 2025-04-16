import random
import sqlite3
import datetime
from faker import Faker
import os
# Updated imports to reflect changes in dbutils.py
from dbutilsV2 import (
    register_student,
    register_specialist,
    add_accommodation,
    add_campus,
    make_reservation,
    update_reservation_status,
    add_rating,
    DB_NAME # Import the DB_NAME constant
)

# Initialize Faker
fake = Faker()

# Sample data (remains the same)
hk_districts = ["Central", "Wan Chai", "Causeway Bay", "North Point", "Quarry Bay",
                "Sai Wan", "Kennedy Town", "Sai Ying Pun", "Sheung Wan", "Admiralty"]
typeList = ['Room', 'Flat', 'Mini hall']

def generate_random_date(start_year=2024, end_year=2026):
    """Generate a random date between start_year and end_year"""
    start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date(end_year, 12, 31)
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    return (start_date + datetime.timedelta(days=random_days)).strftime("%Y-%m-%d")

def generate_address():
    """Generate a random Hong Kong style address string"""
    building_number = random.randint(1, 100)
    floor = random.randint(1, 30)
    unit = random.choice(["A", "B", "C", "D", "E", "F"])
    street = fake.street_name()
    district = random.choice(hk_districts)
    # Simplified address format for demonstration
    return f"{building_number} {street}, {district}, Hong Kong"

def populate_database():
    """Populate the database with sample data using updated functions"""
    print(f"--- Populating Database: {DB_NAME} ---")

    # --- Add Campuses ---
    campuses = [
        ("Main Campus", 22.283454, 114.137432),
        ("Sassoon Road Campus", 22.2675, 114.12881 ),
        ("Swire Institute of Marine Science", 22.20805, 114.26021 ),
        ("Kadoorie Centre", 22.43022, 114.11429),
        ("Faculty of Dentistry", 22.28649, 114.14426),
    ]
    campus_count = 0
    for campus_name, lat, lng in campuses:
        if add_campus(campus_name, lat, lng):
             campus_count += 1
    print(f"Added {campus_count} campuses")

    # --- Add Users (Students and Specialists) ---
    student_ids = []
    specialist_ids = []

    # Add specialists
    for i in range(5):
        name = fake.name()
        email = f"specialist{i+1}@cedars.hku.hk"
        password = fake.password(length=12)
        contact = fake.phone_number() # Generate contact info
        # Use register_specialist
        specialist_id = register_specialist(name, email, password, contact)
        if specialist_id:
            specialist_ids.append(specialist_id)
    print(f"Attempted to add 5 specialists. Added {len(specialist_ids)}")

    # Add students
    for i in range(95):
        name = fake.name()
        email = f"student{i+1}@connect.hku.hk"
        password = fake.password(length=12)
        contact = fake.phone_number() # Generate contact info
        # Use register_student
        student_id = register_student(name, email, password, contact)
        if student_id:
            student_ids.append(student_id)
    print(f"Attempted to add 95 students. Added {len(student_ids)}")

    if not specialist_ids:
        print("Warning: No specialists were added. Accommodations will not have assigned specialists.")
    if not student_ids:
        print("Warning: No students were added. Reservations and ratings cannot be created.")
        return # Exit if no students, as subsequent steps depend on them

    # --- Add Accommodations ---
    accommodation_ids = []
    for i in range(80):
        start_date = generate_random_date()
        start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()

        # End date between 6 months and 2 years after start date
        months_to_add = random.randint(6, 24)
        # Approximate month addition, consider using dateutil.relativedelta for precision if needed
        end_date_obj = start_date_obj + datetime.timedelta(days=30*months_to_add)
        end_date = end_date_obj.strftime("%Y-%m-%d")

        room_type = random.choice(typeList)
        beds = random.randint(1, 4)
        bedrooms = max(1, beds - random.randint(0, 2))

        base_price = 8000
        price_variance = random.uniform(0.8, 1.5)
        price = round(base_price * price_variance * beds, 2) # Round price

        address = generate_address()
        building_name = fake.street_name() + " Building" # Generate building name
        owner_name = fake.company() # Generate owner name
        owner_contact = fake.company_email() # Generate owner contact email

        # Random coordinates around HKU area
        latitude = round(22.283 + random.uniform(-0.02, 0.02), 6) # Limit range slightly
        longitude = round(114.137 + random.uniform(-0.02, 0.02), 6)
        geo_address = f"geo:{latitude},{longitude}" # Generate geo_address

        # Assign a specialist (optional) - 80% chance
        assigned_specialist_id = None
        if specialist_ids and random.random() < 0.8:
             assigned_specialist_id = random.choice(specialist_ids)

        # Use the updated add_accommodation function signature
        accommodation_id = add_accommodation(
            specialist_id=assigned_specialist_id,
            availability_start=start_date,
            availability_end=end_date,
            type=room_type,
            beds=beds,
            bedrooms=bedrooms,
            price=price,
            building_name=building_name, # Pass building_name
            latitude=latitude,
            longitude=longitude,
            address=address, # Pass address
            geo_address=geo_address, # Pass geo_address
            owner_name=owner_name, # Pass owner_name
            owner_contact=owner_contact # Pass owner_contact
        )

        if accommodation_id:
            accommodation_ids.append(accommodation_id)

    print(f"Attempted to add 80 accommodations. Added {len(accommodation_ids)}")

    if not accommodation_ids:
        print("Warning: No accommodations were added. Cannot create reservations or ratings.")
        return # Exit if no accommodations

    # --- Make Reservations ---
    reservation_ids = []
    reserved_accommodation_info = [] # Store (res_id, user_id, acc_id) for rating

    # Shuffle accommodation IDs to randomize which ones are reserved
    random.shuffle(accommodation_ids)
    # Attempt to reserve up to 60 or max available accommodations
    num_reservations_to_make = min(60, len(accommodation_ids))
    accommodations_to_reserve = accommodation_ids[:num_reservations_to_make]

    for accommodation_id in accommodations_to_reserve:
        if not student_ids: break # Should not happen based on earlier check, but safe guard
        student_id = random.choice(student_ids)

        # Make reservation using the updated function
        reservation_id = make_reservation(student_id, accommodation_id)

        if reservation_id:
            reservation_ids.append(reservation_id)
            # Randomize reservation status
            status = random.choice(['pending', 'confirmed', 'completed', 'completed', 'completed'])
            if update_reservation_status(reservation_id, status):
                 # If completed, store info needed for potential rating
                 if status == 'completed':
                     reserved_accommodation_info.append({
                         "reservation_id": reservation_id,
                         "user_id": student_id,
                         "accommodation_id": accommodation_id
                     })

    print(f"Attempted to make {num_reservations_to_make} reservations. Made {len(reservation_ids)}")

    # --- Add Ratings for Completed Reservations ---
    rating_count = 0
    # We already collected info for completed reservations in reserved_accommodation_info
    completed_reservations_info = [
        info for info in reserved_accommodation_info
        if info.get("reservation_id") # Basic check if info was stored correctly
        # We can optionally re-query the DB to be absolutely sure they are 'completed'
        # but for this script, we rely on the status set above.
    ]

    # Add ratings for ~80% of completed reservations
    for res_info in completed_reservations_info:
        if random.random() < 0.8: # 80% chance
            user_id = res_info["user_id"]
            accommodation_id = res_info["accommodation_id"]
            rating_value = random.randint(0, 5) # Rating 0-5
            comment = fake.sentence() if random.random() < 0.6 else None # 60% chance of comment

            # Use the updated add_rating function
            rating_id = add_rating(user_id, accommodation_id, rating_value, comment)
            if rating_id:
                rating_count += 1

    print(f"Attempted to add ratings for completed reservations. Added {rating_count} ratings")

    # --- Final Statistics ---
    print("\n--- Database Population Summary ---")
    # Use the get_stats function if available and reliable, otherwise use script counts
    try:
        from dbutils import get_stats
        stats = get_stats()
        if stats:
            print("Stats from dbutils.get_stats():")
            for key, value in stats.items():
                 print(f"- {key.replace('_', ' ').capitalize()}: {value}")
        else:
             raise ImportError # Fallback if get_stats fails
    except (ImportError, AttributeError, Exception) as e:
        print(f"(Could not fetch stats via dbutils, using script counts - Error: {e})")
        print(f"- Students added: {len(student_ids)}")
        print(f"- Specialists added: {len(specialist_ids)}")
        print(f"- Accommodations added: {len(accommodation_ids)}")
        # Note: reservation/rating counts below might differ slightly if errors occurred during processing
        print(f"- Reservations made: {len(reservation_ids)}")
        print(f"- Ratings added: {rating_count}")

if __name__ == "__main__":
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the database file
    db_path = os.path.join(script_dir, DB_NAME) # Use a new db name
    print(f"Checking for database file: {db_path}")
    # Check if database exists and has tables
    try:
        # Connect to the correct database name
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Check for essential tables based on the new schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('Student', 'Specialist', 'Accommodation', 'Reservation', 'Rating', 'Campus')")
        tables = cursor.fetchall()
        cursor.close()
        conn.close()

        # Expecting 6 tables now
        if len(tables) < 6:
            print(f"\nDatabase '{DB_NAME}' structure seems incomplete (found {len(tables)}/6 essential tables).")
            print("Please run the updated create_database script first.")
        else:
            print(f"Database structure seems OK. Proceeding with data population...")
            populate_database()
            print("\n--- Makeup Data Script Finished ---")
    except sqlite3.OperationalError as e:
         print(f"\nDatabase error: {e}. Could not connect or query '{DB_NAME}'.")
         print("Please ensure the database exists and the path is correct. Run the updated create_database script first.")
    except Exception as e:
         print(f"\nAn unexpected error occurred: {e}")
         print("Please check the scripts and database setup.")