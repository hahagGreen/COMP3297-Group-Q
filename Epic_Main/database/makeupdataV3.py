import random
import sqlite3
import datetime
from faker import Faker
import os
# Updated imports to reflect changes in dbutilsV3.py
# Added get_db_connection for the workaround, although we'll try to avoid it
from dbutilsV3 import (
    register_student,
    register_specialist,
    add_accommodation,
    add_campus,
    add_accommodation_offering, # Added import
    make_reservation,
    update_reservation_status,
    add_rating,
    get_stats, # Import get_stats directly
    get_db_connection, # Import the connection function
    DB_NAME # Import the DB_NAME constant (should be 'unihaven_sprint3.db')
)

# Initialize Faker
fake = Faker()

# Sample data (remains the same)
hk_districts = ["Central", "Wan Chai", "Causeway Bay", "North Point", "Quarry Bay",
                "Sai Wan", "Kennedy Town", "Sai Ying Pun", "Sheung Wan", "Admiralty"]
typeList = ['Room', 'Flat', 'Mini hall']

def generate_random_date(start_year=2025, end_year=2027): # Adjusted years slightly
    """Generate a random date between start_year and end_year"""
    start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date(end_year, 12, 31)
    try:
        days_between = (end_date - start_date).days
        random_days = random.randint(0, days_between)
        return (start_date + datetime.timedelta(days=random_days)).strftime("%Y-%m-%d")
    except ValueError: # Handle potential date range issues
        return datetime.date(start_year, 1, 1).strftime("%Y-%m-%d")


def generate_address_details():
    """Generate random HK style address components"""
    building_number = random.randint(1, 100)
    floor = random.randint(1, 30)
    flat_unit = random.choice(["A", "B", "C", "D"])
    street = fake.street_name()
    district = random.choice(hk_districts)

    full_address = f"{building_number} {street}, {district}, Hong Kong"
    # Ensure street name has parts to avoid index error if street name is simple
    building_name_base = street.split()[0] if ' ' in street else street
    building_name = f"{building_name_base} Tower" # Simple building name based on street

    # V5 specific fields
    flat_number = f"{floor}{flat_unit}"
    floor_number = str(floor)
    room_number = None # Often None for Flats/Mini halls, maybe add logic for 'Room' type?
    if random.random() < 0.2: # 20% chance of having a room number even if flat
       room_number = f"R{random.randint(1,5)}"

    return full_address, building_name, flat_number, floor_number, room_number

def populate_database(num_students=95, num_specialists=5, num_accommodations=80, num_reservations=60):
    """Populate the database with sample data using V3 functions"""
    print(f"--- Populating Database: {DB_NAME} ---")

    # --- Add Campuses ---
    campuses_data = [
        ("Main Campus", 22.28405, 114.13784),
        ("Sassoon Road Campus", 22.2675, 114.12881 ),
        ("Swire Institute of Marine Science", 22.20805, 114.26021),
        ("Kadoorie Centre", 22.43022, 114.11429),
        ("Faculty of Dentistry", 22.28649, 114.14426)
    ]
    # --- FIX: Store name -> (id, lat, lng) mapping ---
    campus_details = {}
    campus_id_list = [] # Keep a separate list of just IDs for random assignment later
    campus_count = 0
    print("\n--- Adding Campuses ---")
    for campus_name, lat, lng in campuses_data:
        campus_id = add_campus(campus_name, lat, lng)
        if campus_id:
             # Store the ID, lat, and lng associated with the name
             campus_details[campus_name] = {'id': campus_id, 'lat': lat, 'lng': lng}
             campus_id_list.append(campus_id) # Add ID to the list
             campus_count += 1
    print(f"Added {campus_count} campuses")
    if not campus_details: # Check if the dictionary is populated
        print("ERROR: No campuses added. Cannot proceed.")
        return

    # campus_id_list is already populated above

    # --- Add Users (Students and Specialists) ---
    student_ids = []
    specialist_ids = []

    # Add specialists
    print("\n--- Adding Specialists ---")
    for i in range(num_specialists):
        name = fake.name()
        email = f"specialist.v3.{i+1}@cedars.hku.hk"
        password = fake.password(length=12)
        contact = fake.phone_number()
        # Assign to a random campus using the ID list
        assigned_campus_id = random.choice(campus_id_list)
        specialist_id = register_specialist(name, email, password, contact, assigned_campus_id)
        if specialist_id:
            specialist_ids.append(specialist_id)
    print(f"Attempted to add {num_specialists} specialists. Added {len(specialist_ids)}")

    # Add students
    print("\n--- Adding Students ---")
    for i in range(num_students):
        name = fake.name()
        email = f"student.v3.{i+1}@connect.hku.hk"
        password = fake.password(length=12)
        contact = fake.phone_number()
        # Assign to a random campus using the ID list
        assigned_campus_id = random.choice(campus_id_list)
        student_id = register_student(name, email, password, contact, assigned_campus_id)
        if student_id:
            student_ids.append(student_id)
    print(f"Attempted to add {num_students} students. Added {len(student_ids)}")

    if not specialist_ids:
        print("Warning: No specialists were added. Accommodation offerings cannot be created.")
    if not student_ids:
        print("Warning: No students were added. Reservations and ratings cannot be created.")
        # Don't exit yet, accommodation can still be added

    # --- Add Accommodations ---
    print("\n--- Adding Accommodations ---")
    accommodation_ids = []
    # --- FIX: Use the campus_details dictionary created earlier ---
    campus_names_list = list(campus_details.keys()) # Get a list of campus names to choose from

    for i in range(num_accommodations):
        start_date = generate_random_date()
        start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        months_to_add = random.randint(6, 24)
        end_date_obj = start_date_obj + datetime.timedelta(days=30*months_to_add) # Approx end date
        end_date = end_date_obj.strftime("%Y-%m-%d")

        room_type = random.choice(typeList)
        beds = random.randint(1, 4)
        bedrooms = max(1, beds - random.randint(0, 2))

        base_price = 8000
        price_variance = random.uniform(0.7, 1.6) # Adjusted variance slightly
        price = round(base_price * price_variance * (1 + beds*0.2 + bedrooms*0.1), 2) # More complex price

        # Generate V5 address details
        full_address, building_name, flat_number, floor_number, room_number = generate_address_details()

        owner_name = fake.company()
        owner_contact = fake.company_email()

        # --- FIX: Get coords from the campus_details dictionary ---
        random_campus_name = random.choice(campus_names_list)
        # Retrieve the pre-stored lat and lng for the chosen campus
        base_lat = campus_details[random_campus_name]['lat']
        base_lng = campus_details[random_campus_name]['lng']
        # Removed the inefficient database query block

        # Generate coordinates near the chosen campus
        latitude = round(base_lat + random.uniform(-0.015, 0.015), 6) # Smaller radius
        longitude = round(base_lng + random.uniform(-0.015, 0.015), 6)
        geo_address = f"geo:{latitude},{longitude}"

        # Use the updated add_accommodation function signature (V3)
        accommodation_id = add_accommodation(
            availability_start=start_date,
            availability_end=end_date,
            type=room_type,
            beds=beds,
            bedrooms=bedrooms,
            price=price,
            building_name=building_name,
            latitude=latitude,
            longitude=longitude,
            address=full_address, # Use generated full address
            geo_address=geo_address,
            owner_name=owner_name,
            owner_contact=owner_contact,
            # --- V5 Specific ---
            flat_number=flat_number,
            floor_number=floor_number,
            room_number=room_number
            # specialist_id is removed
        )

        if accommodation_id:
            accommodation_ids.append(accommodation_id)

            # --- Add Accommodation Offering ---
            # For each added accommodation, create 1-2 offerings by specialists at nearby campuses
            num_offerings_to_add = random.randint(1, 2)
            possible_specialists = specialist_ids # Use all available specialists
            # Use the list of campus IDs directly
            possible_campuses = campus_id_list

            if possible_specialists and possible_campuses:
                added_offerings_count = 0
                attempts = 0
                # Keep track of offerings added for this accommodation to avoid duplicates
                added_offerings_for_acc = set()
                while added_offerings_count < num_offerings_to_add and attempts < 5: # Limit attempts
                    chosen_specialist_id = random.choice(possible_specialists)
                    chosen_campus_id = random.choice(possible_campuses)

                    # Prevent adding the exact same offering (acc, campus, spec) twice
                    offering_key = (accommodation_id, chosen_campus_id, chosen_specialist_id)
                    if offering_key not in added_offerings_for_acc:
                        # Use the new function
                        offering_id = add_accommodation_offering(
                            accommodation_id=accommodation_id,
                            campus_id=chosen_campus_id,
                            specialist_id=chosen_specialist_id
                        )
                        if offering_id:
                            added_offerings_count += 1
                            added_offerings_for_acc.add(offering_key) # Record successful addition
                    attempts += 1
                # Optional: print(f"   Added {added_offerings_count} offerings for Acc ID {accommodation_id}")


    print(f"Attempted to add {num_accommodations} accommodations. Added {len(accommodation_ids)}")

    if not accommodation_ids or not student_ids:
        print("Warning: Cannot create reservations or ratings due to missing accommodations or students.")
        # --- Final Statistics before exiting early ---
        print("\n--- Database Population Summary (using get_stats) ---")
        stats = get_stats()
        if stats:
            for key, value in stats.items():
                 print(f"- {key.replace('_', ' ').capitalize()}: {value}")
        else:
            print("Could not fetch final statistics using get_stats(). Check dbutilsV3.")
        return # Exit if no accommodations or students


    # --- Make Reservations ---
    print("\n--- Making Reservations ---")
    reservation_ids = []
    reserved_accommodation_info = [] # Store (res_id, user_id, acc_id) for rating

    random.shuffle(accommodation_ids)
    num_reservations_to_make = min(num_reservations, len(accommodation_ids))
    accommodations_to_reserve = accommodation_ids[:num_reservations_to_make]

    reservations_made_count = 0
    for accommodation_id in accommodations_to_reserve:
        student_id = random.choice(student_ids)

        # Make reservation using the V3 function
        reservation_id = make_reservation(student_id, accommodation_id) # status defaults to 'pending'

        if reservation_id:
            reservations_made_count += 1
            reservation_ids.append(reservation_id)
            # Randomize reservation status AFTER creation
            # Make 'completed' more likely for rating purposes
            status = random.choice(['pending', 'confirmed', 'completed', 'completed', 'completed', 'canceled'])
            if update_reservation_status(reservation_id, status):
                 # If completed, store info needed for potential rating
                 # Check status again *after* update call, as 'canceled' might delete the row
                 if status == 'completed':
                     # Need to check if reservation still exists if update_status could have deleted it
                     conn_check = get_db_connection()
                     cursor_check = conn_check.cursor()
                     cursor_check.execute("SELECT status FROM Reservation WHERE reservation_id = ?", (reservation_id,))
                     res_status_after_update = cursor_check.fetchone()
                     cursor_check.close()
                     conn_check.close()
                     # Only add if it's confirmed to be completed
                     if res_status_after_update and res_status_after_update['status'] == 'completed':
                         reserved_accommodation_info.append({
                             "reservation_id": reservation_id, # Store ID
                             "user_id": student_id,
                             "accommodation_id": accommodation_id,
                             "final_status": 'completed'
                         })
                 elif status == 'canceled':
                     # Optional: note that it was canceled if needed elsewhere
                     pass # Row is likely deleted by update_reservation_status

    print(f"Attempted to make {num_reservations_to_make} reservations. Made {reservations_made_count}")

    # --- Add Ratings for Completed Reservations ---
    print("\n--- Adding Ratings ---")
    # Filter the info list for entries we marked as completed
    completed_reservations_info = [
        info for info in reserved_accommodation_info if info.get("final_status") == 'completed'
    ]

    # Add ratings for ~80% of completed reservations
    ratings_added_count = 0
    for res_info in completed_reservations_info:
        if random.random() < 0.8: # 80% chance
            user_id = res_info["user_id"]
            accommodation_id = res_info["accommodation_id"]
            rating_value = random.randint(1, 5) # Rating 1-5 (0 seems harsh for random data)
            comment = fake.sentence() if random.random() < 0.6 else None

            # Use the V3 add_rating function
            rating_id = add_rating(user_id, accommodation_id, rating_value, comment)
            if rating_id:
                ratings_added_count += 1

    print(f"Attempted to add ratings for {len(completed_reservations_info)} completed reservations. Added {ratings_added_count} ratings")

    # --- Final Statistics ---
    print("\n--- Database Population Summary (using get_stats) ---")
    stats = get_stats()
    if stats:
        for key, value in stats.items():
             print(f"- {key.replace('_', ' ').capitalize()}: {value}")
    else:
        print("Could not fetch final statistics using get_stats(). Check dbutilsV3.")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, DB_NAME) # Use DB_NAME from dbutilsV3
    print(f"Checking for V5 database file: {db_path}")

    try:
        # Ensure connection uses row_factory for dictionary access if needed elsewhere
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Check for essential tables from V5 schema
        required_tables = ['Campus', 'Student', 'Specialist', 'Accommodation', 'AccommodationOffering', 'Reservation', 'Rating']
        placeholders = ','.join(['?'] * len(required_tables))
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name IN ({placeholders})", required_tables)
        tables = cursor.fetchall()
        cursor.close()
        conn.close()

        found_table_names = {row['name'] for row in tables} # Access by name
        missing_tables = set(required_tables) - found_table_names

        if missing_tables:
            print(f"\nDatabase '{DB_NAME}' structure seems incomplete.")
            print(f"Missing essential V5 tables: {', '.join(missing_tables)}")
            print("Please run the create_dbV5.py script first.")
        else:
            print(f"Database structure seems OK (found {len(found_table_names)}/{len(required_tables)} V5 tables). Proceeding with data population...")
            populate_database() # Call the main population function
            print("\n--- Makeup Data V3 Script Finished ---")

    except sqlite3.OperationalError as e:
         print(f"\nDatabase error: {e}. Could not connect or query '{DB_NAME}'.")
         print("Please ensure the database exists and the path is correct. Run create_dbV5.py first.")
    except Exception as e:
         print(f"\nAn unexpected error occurred during setup or population: {e}")
         import traceback
         traceback.print_exc() # Print detailed traceback for debugging
         print("Please check the scripts and database setup.")
