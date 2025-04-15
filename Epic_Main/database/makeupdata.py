import random
import sqlite3
import datetime
from faker import Faker
from dbutils import register_user, add_accommodation, add_campus, make_reservation, update_reservation_status, add_rating

# Initialize Faker
fake = Faker()

# Sample data
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
    """Generate a random Hong Kong address"""
    building_number = random.randint(1, 100)
    floor = random.randint(1, 30)
    unit = random.choice(["A", "B", "C", "D", "E", "F"])
    street = fake.street_name()
    district = random.choice(hk_districts)
    return f"{building_number} {street}, {unit}/{floor}, {district}, Hong Kong"

def populate_database():
    """Populate the database with sample data"""
    # Add HKU campuses
    #("Centennial Campus", 22.282439, 114.135433),
    #("Medical Campus", 22.270257, 114.131789),
    campuses = [
        ("Main Campus", 22.283454, 114.137432),
        ("Sassoon Road Campus", 22.2675, 114.12881 ),
        ("Swire Institute of Marine Science", 22.20805, 114.26021 ),
        ("Kadoorie Centre", 22.43022, 114.11429),
        ("Faculty of Dentistry", 22.28649, 114.14426),
    ]
    
    for campus_name, lat, lng in campuses:
        add_campus(campus_name, lat, lng)
    
    print("Added 5 campuses")
    
    # Add 100 users (95 students and 5 specialists)
    student_ids = []
    specialist_ids = []
    
    # Add specialists
    for i in range(5):
        name = fake.name()
        email = f"specialist{i+1}@cedars.hku.hk"
        password = fake.password(length=12)
        specialist_id = register_user(name, email, password, "Specialist")
        if specialist_id:
            specialist_ids.append(specialist_id)
    
    print(f"Added {len(specialist_ids)} specialists")
    
    # Add students
    for i in range(95):
        name = fake.name()
        email = f"student{i+1}@connect.hku.hk"
        password = fake.password(length=12)
        student_id = register_user(name, email, password, "Student")
        if student_id:
            student_ids.append(student_id)
    
    print(f"Added {len(student_ids)} students")
    
    # Add 80 accommodations
    accommodation_ids = []
    
    for i in range(80):
        start_date = generate_random_date()
        
        # End date between 6 months and 2 years after start date
        start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        months_to_add = random.randint(6, 24)
        end_date_obj = start_date_obj + datetime.timedelta(days=30*months_to_add)
        end_date = end_date_obj.strftime("%Y-%m-%d")
        
        room_type = random.choice(typeList)
        beds = random.randint(1, 4)
        bedrooms = max(1, beds - random.randint(0, 2))  # Ensure bedrooms <= beds
        
        # Price based on number of beds
        base_price = 8000
        price_variance = random.uniform(0.8, 1.5)  # Variable pricing
        price = base_price * price_variance * beds
        
        address = generate_address()
        
        # Random coordinates around HKU
        latitude = 22.28 + random.uniform(-0.05, 0.05)
        longitude = 114.13 + random.uniform(-0.05, 0.05)
        
        accommodation_id = add_accommodation(
            start_date, end_date, room_type, beds, bedrooms, price, address, 
            latitude, longitude, address
        )
        
        if accommodation_id:
            accommodation_ids.append(accommodation_id)
    
    print(f"Added {len(accommodation_ids)} accommodations")
    
    # Make 60 reservations
    reservation_ids = []
    
    # Shuffle accommodation IDs to randomize which ones are reserved
    random.shuffle(accommodation_ids)
    accommodations_to_reserve = accommodation_ids[:60]
    
    for accommodation_id in accommodations_to_reserve:
        # Random student makes the reservation
        student_id = random.choice(student_ids)
        
        # Make reservation
        reservation_id = make_reservation(student_id, accommodation_id)
        
        if reservation_id:
            reservation_ids.append(reservation_id)
            
            # Randomize reservation status
            status = random.choice(['pending', 'confirmed', 'completed', 'completed', 'completed'])  # Higher chance of completed
            update_reservation_status(reservation_id, status)
    
    print(f"Added {len(reservation_ids)} reservations")
    
    # Add ratings for completed reservations
    rating_count = 0
    
    # Connect to check completed reservations
    conn = sqlite3.connect('unihaven.db')
    cursor = conn.cursor()
    cursor.execute("SELECT reservation_id FROM Reservation WHERE status='completed'")
    completed_reservations = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Add ratings for 80% of completed reservations
    for reservation in completed_reservations:
        if random.random() < 0.8:  # 80% chance of rating
            reservation_id = reservation[0]
            rating_value = random.randint(1, 5)
            
            rating_id = add_rating(reservation_id, rating_value)
            if rating_id:
                rating_count += 1
    
    print(f"Added {rating_count} ratings")
    
    # Print statistics
    print("\nDatabase populated successfully!")
    print(f"- {len(student_ids)} students")
    print(f"- {len(specialist_ids)} specialists")
    print(f"- {len(accommodation_ids)} accommodations")
    print(f"- {len(reservation_ids)} reservations")
    print(f"- {rating_count} ratings")

if __name__ == "__main__":
    # Check if database exists and has tables
    try:
        conn = sqlite3.connect('unihaven.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if len(tables) < 5:
            print("Please run create_db.py first to create the database structure.")
        else:
            populate_database()
    except sqlite3.Error:
        print("Database error. Please run create_db.py first to create the database structure.")