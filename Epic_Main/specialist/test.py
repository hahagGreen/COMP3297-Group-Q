from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from django.db import connection
# Import models from Reservation app where they are also defined
from .models import Campus, Student, Specialist, Accommodation, AccommodationOffering, Reservation, Rating


class SpecialistAPITests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create tables that are marked as managed=False
        with connection.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Campus (
                    campus_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    latitude FLOAT NOT NULL,
                    longitude FLOAT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Student (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    contact VARCHAR(255) NULL,
                    campus_id INTEGER NULL REFERENCES Campus(campus_id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Specialist (
                    specialist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    contact VARCHAR(255) NOT NULL,
                    campus_id INTEGER NULL REFERENCES Campus(campus_id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Accommodation (
                    accommodation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    availability_start DATE NOT NULL,
                    availability_end DATE NOT NULL,
                    type VARCHAR(20) NOT NULL,
                    beds INTEGER NOT NULL,
                    bedrooms INTEGER NOT NULL,
                    price FLOAT NOT NULL,
                    building_name VARCHAR(255) NOT NULL,
                    latitude FLOAT NOT NULL,
                    longitude FLOAT NOT NULL,
                    address TEXT NOT NULL,
                    geo_address TEXT NULL,
                    room_number VARCHAR(10) NULL,
                    flat_number VARCHAR(10) NOT NULL,
                    floor_number VARCHAR(10) NOT NULL,
                    owner_name VARCHAR(255) NOT NULL,
                    owner_contact VARCHAR(255) NOT NULL,
                    is_reserved BOOLEAN DEFAULT 0 NOT NULL,
                    average_rating FLOAT DEFAULT 0,
                    rating_count INTEGER DEFAULT 0
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS AccommodationOffering (
                    offering_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    accommodation_id INTEGER REFERENCES Accommodation(accommodation_id),
                    campus_id INTEGER REFERENCES Campus(campus_id),
                    specialist_id INTEGER REFERENCES Specialist(specialist_id),
                    UNIQUE (accommodation_id, campus_id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Reservation (
                    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES Student(user_id),
                    accommodation_id INTEGER REFERENCES Accommodation(accommodation_id),
                    status VARCHAR(20) NOT NULL,
                    created_date DATE DEFAULT CURRENT_DATE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Rating (
                    rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES Student(user_id),
                    accommodation_id INTEGER REFERENCES Accommodation(accommodation_id),
                    rating INTEGER NOT NULL,
                    comment TEXT NULL,
                    date DATE NOT NULL
                )
            ''')

    @classmethod
    def tearDownClass(cls):
        # Drop the tables we created
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS Rating")
            cursor.execute("DROP TABLE IF EXISTS Reservation")
            cursor.execute("DROP TABLE IF EXISTS AccommodationOffering")
            cursor.execute("DROP TABLE IF EXISTS Accommodation")
            cursor.execute("DROP TABLE IF EXISTS Specialist")
            cursor.execute("DROP TABLE IF EXISTS Student")
            cursor.execute("DROP TABLE IF EXISTS Campus")
        super().tearDownClass()

    def setUp(self):
        # 校区
        self.campus_hku = Campus.objects.create(
            name='HKU', latitude=22.283, longitude=114.137
        )
        self.campus_cuhk = Campus.objects.create(
            name='CUHK', latitude=22.419, longitude=114.210
        )
        # 用户
        self.student = Student.objects.create(
            name="TestStudent", email="student@example.com", password="test", campus=self.campus_hku
        )
        self.specialist = Specialist.objects.create(
            name="TestSpecialist", email="specialist@example.com", password="test", campus=self.campus_hku, contact="123456"
        )
        
        # 房源
        self.accommodation = Accommodation.objects.create(
            availability_start=timezone.now().date(),
            availability_end=timezone.now().date(),
            type="Flat",
            beds=2,
            bedrooms=1,
            price=1000.0,
            building_name="Test Building",
            latitude=22.283,
            longitude=114.137,
            address="123 Test Street",
            geo_address="Test Area, HK",
            room_number=None,
            flat_number="A",
            floor_number="3",
            owner_name="Test Owner",
            owner_contact="12345678",
            is_reserved=False
        )
        
        # 挂载到校区
        self.offering = AccommodationOffering.objects.create(
            accommodation=self.accommodation,
            campus=self.campus_hku,
            specialist=self.specialist
        )
        
        # 准备几个不同状态的预约
        self.pending_reservation = Reservation.objects.create(
            user=self.student,
            accommodation=self.accommodation,
            status=Reservation.PENDING
        )
        
        # Create a second accommodation for additional tests
        self.accommodation2 = Accommodation.objects.create(
            availability_start=timezone.now().date(),
            availability_end=timezone.now().date(),
            type="Room",
            beds=1,
            bedrooms=1,
            price=500.0,
            building_name="Test Building 2",
            latitude=22.284,
            longitude=114.138,
            address="456 Test Street",
            geo_address="Test Area 2, HK",
            room_number="101",
            flat_number="B",
            floor_number="5",
            owner_name="Test Owner 2",
            owner_contact="87654321",
            is_reserved=True
        )
        
        self.confirmed_reservation = Reservation.objects.create(
            user=self.student,
            accommodation=self.accommodation2,
            status=Reservation.CONFIRMED
        )
        
        # 创建一个已完成的预约
        self.completed_reservation = Reservation.objects.create(
            user=self.student,
            accommodation=self.accommodation,
            status=Reservation.COMPLETED
        )
        
        # 设置APIClient，模拟specialist登录
        self.client = APIClient()
        self.client.force_authenticate(user=self.specialist)

    def test_view_active_reservations(self):
        """Test the API to view active reservations"""
        url = reverse('api_active')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that we got the pending and confirmed reservations but not completed ones
        data = response.json()
        self.assertEqual(len(data['reservations']), 2)
        reservation_statuses = [r['status'] for r in data['reservations']]
        self.assertIn(Reservation.PENDING, reservation_statuses)
        self.assertIn(Reservation.CONFIRMED, reservation_statuses)
        self.assertNotIn(Reservation.COMPLETED, reservation_statuses)

    def test_cancel_reservation(self):
        """Test the API to cancel a reservation"""
        url = reverse('api_cancel')
        # Modified to send the reservation_id as a query parameter instead of in the request body
        response = self.client.post(f"{url}?reservation_id={self.pending_reservation.reservation_id}")
        
        # Now that the bug is fixed, we expect a successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_reservation.refresh_from_db()
        self.assertEqual(self.pending_reservation.status, Reservation.CANCELED)
        
        # Check that accommodation is no longer marked as reserved
        self.accommodation.refresh_from_db()
        self.assertFalse(self.accommodation.is_reserved)

    def test_cancel_nonexistent_reservation(self):
        """Test canceling a reservation that doesn't exist"""
        url = reverse('api_cancel')
        # Updated to use query parameter instead of JSON body
        response = self.client.post(f"{url}?reservation_id=9999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_cancel_without_reservation_id(self):
        """Test canceling without providing a reservation ID"""
        url = reverse('api_cancel')
        # No reservation_id parameter is provided
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_modify_reservation_status_to_confirmed(self):
        """Test modifying a reservation status to confirmed"""
        url = reverse('api_modify')
        response = self.client.post(
            f"{url}?reservation_id={self.pending_reservation.reservation_id}&status={Reservation.CONFIRMED}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_reservation.refresh_from_db()
        self.assertEqual(self.pending_reservation.status, Reservation.CONFIRMED)
        
        # Check that accommodation is marked as reserved
        self.accommodation.refresh_from_db()
        self.assertTrue(self.accommodation.is_reserved)

    def test_modify_reservation_status_to_canceled(self):
        """Test modifying a reservation status to canceled"""
        url = reverse('api_modify')
        response = self.client.post(
            f"{url}?reservation_id={self.confirmed_reservation.reservation_id}&status={Reservation.CANCELED}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.confirmed_reservation.refresh_from_db()
        self.assertEqual(self.confirmed_reservation.status, Reservation.CANCELED)

    def test_modify_reservation_invalid_status(self):
        """Test modifying a reservation with an invalid status"""
        url = reverse('api_modify')
        response = self.client.post(
            f"{url}?reservation_id={self.pending_reservation.reservation_id}&status=invalid_status"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid status', response.json()['error'])

    def test_modify_nonexistent_reservation(self):
        """Test modifying a reservation that doesn't exist"""
        url = reverse('api_modify')
        response = self.client.post(
            f"{url}?reservation_id=9999&status={Reservation.CONFIRMED}"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_modify_without_required_parameters(self):
        """Test modifying without providing required parameters"""
        url = reverse('api_modify')
        # Missing status
        response1 = self.client.post(
            f"{url}?reservation_id={self.pending_reservation.reservation_id}"
        )
        self.assertEqual(response1.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing reservation_id
        response2 = self.client.post(
            f"{url}?status={Reservation.CONFIRMED}"
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing both
        response3 = self.client.post(url)
        self.assertEqual(response3.status_code, status.HTTP_400_BAD_REQUEST)
    
