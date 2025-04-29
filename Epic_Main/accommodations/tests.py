from datetime import timedelta
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient, APIRequestFactory
from rest_framework import status
from django.utils import timezone
from .models import (
    Campus, Student, Specialist, Accommodation, AccommodationOffering,
    Reservation, Rating
)
from .views import ApiViewDetails, ApiSearchView, ApiRateView

class AccommodationTests(APITestCase):
    def setUp(self):
        self.student = Student.objects.create(
            student_id=1,
            name="John Doe",
            email="bruh@gmail.com",
            password="password123",
            contact="12345678",
            campus=Campus.objects.create(
                campus_id=1,
                name="Main Campus",
                latitude=22.283,
                longitude=114.137
            )
        )
        self.factory = APIRequestFactory()
        self.accommodation = Accommodation.objects.create(
            availability_start=timezone.now().date(),
            availability_end=timezone.now().date(),
            type="Flat",
            beds=2,
            bedrooms=1,
            price=1000.0,
            building_name="Happy Building",
            latitude=22.283,
            longitude=114.137,
            address="123 Queen's Road",
            geo_address="Central, HK",
            room_number=None,
            flat_number="A",
            floor_number="3",
            owner_name="Mr. Chan",
            owner_contact="12345678",
            is_reserved=False
        )
        self.data = {"userId": 1, "accId": 1}
        self.accId = "1"

    
    def test_accommodation_view(self):
        """
        Test the accommodation view to ensure it returns the correct data.
        """
        request = self.factory.post("accommodations/api_view?accId=1", self.data)
        view = ApiViewDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'],'1')
        self.assertEqual(response.data['type'], 'Flat')
        self.assertEqual(response.data['numOfBeds'], 2)
        self.assertEqual(response.data['numOfBedrooms'], 1)
        self.assertEqual(response.data['price'], 1000.0)
        self.assertEqual(response.data['building_name'], 'Happy Building')
        self.assertEqual(response.data['latitude'], 22.283)
        self.assertEqual(response.data['longitude'], 114.137)
        self.assertEqual(response.data['address'], '123 Queen\'s Road')
        self.assertEqual(response.data['geo_address'], 'Central, HK')
        self.assertEqual(response.data['room_number'], None)
        self.assertEqual(response.data['flat_number'], 'A')
        self.assertEqual(response.data['floor_number'], '3')
        self.assertEqual(response.data['owner_name'], 'Mr. Chan')
        self.assertEqual(response.data['owner_contact'], '12345678')
        self.assertEqual(response.data['is_reserved'], 'no')
        
    
    def test_accommodation_userNotFound(self):
        """
        Test the accommodation view when the user is not found.
        """
        request = self.factory.post("accommodations/api_view?accId=1", {'userId': 999})
        view = ApiViewDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 404)

    def test_accommodation_accommodationNotFound(self):
        """
        Test the accommodation view when the accommodation is not found.
        """
        request = self.factory.post("accommodations/api_view?accId=999", {'userId': 1})
        view = ApiViewDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 404)
    
    def test_accommodation_accommodationIDIsNotGiven(self):
        """
        Test the accommodation view when the accommodation ID is not given.
        """
        request = self.factory.post("accommodations/api_view?accId=", {'userId': 1})
        view = ApiViewDetails.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 400)

class AccommodationRateTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.accommodation = Accommodation.objects.create(
            availability_start=timezone.now().date(),
            availability_end=timezone.now().date(),
            type="Flat",
            beds=2,
            bedrooms=1,
            price=1000.0,
            building_name="Happy Building",
            latitude=22.283,
            longitude=114.137,
            address="123 Queen's Road",
            geo_address="Central, HK",
            room_number=None,
            flat_number="A",
            floor_number="3",
            owner_name="Mr. Chan",
            owner_contact="12345678",
            is_reserved=False,
            average_rating=4.5,
            rating_count=10
        )
        self.student = Student.objects.create(
            student_id=1,
            name="John Doe",
            email="bruh@gmail.com",
            password="password123",
            contact="12345678",
            campus=Campus.objects.create(
                campus_id=1,
                name="Main Campus",
                latitude=22.283,
                longitude=114.137
            )
        )
        self.userId = 1
        self.accId = 1
        self.date = timezone.now().date()
        self.comment = "Great place!"
        self.rating = 4
        
    def test_accommodation_giveRating(self):
        """
        Test the rating system to ensure it receive the correct data.
        """
        request = self.factory.post(f"accommodations/api_rate?userId={self.userId}&accId={self.accId}&rating={self.rating}&date={self.date}&comment={self.comment}")
        view = ApiRateView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Rating updated successfully')
        self.assertEqual(response.data['data'][0]['rating_id'], 1)
        self.assertEqual(response.data['data'][0]['rating'], 4)
        self.assertEqual(response.data['data'][0]['comment'], 'Great place!')

        
    def test_accommodation_updatedRating(self):
        """
        Test the rating system to ensure it updates the average rating and count correctly.
        """
        request = self.factory.post(f"accommodations/api_rate?userId={self.userId}&accId={self.accId}&rating={self.rating}&date={self.date}&comment={self.comment}")
        view = ApiRateView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Rating updated successfully')
        self.assertEqual(response.data['data'][1]['average_rating'], str(4.45))
        self.assertEqual(response.data['data'][1]['rating_count'], 11)
        
    def test_accommodation_userNotFound(self):
        """
        Test the rating system when the user is not found.
        """
        request = self.factory.post(f"accommodations/api_rate?userId=999&accId={self.accId}&rating={self.rating}&date={self.date}&comment={self.comment}")
        view = ApiRateView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 404)
    def test_accommodation_accommodationNotFound(self):
        """
        Test the rating system when the accommodation is not found.
        """
        request = self.factory.post(f"accommodations/api_rate?userId={self.userId}&accId=999&rating={self.rating}&date={self.date}&comment={self.comment}")
        view = ApiRateView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 404)
        

class AccommodationSearchTests(APITestCase):
    def setUp(self):
        # Use APIClient for simulating requests to the endpoint URL
        self.client = APIClient()
        self.search_url = reverse('api_search')

        # Create Campus
        self.campus1 = Campus.objects.create(
            campus_id=1,
            name="Main Campus",
            latitude=22.336,  # Example coordinates for HKBU area
            longitude=114.180
        )

        # Create Accommodations
        today = timezone.now().date()
        self.acc1 = Accommodation.objects.create(
            accommodation_id=1,
            availability_start=today - timedelta(days=10),
            availability_end=today + timedelta(days=20),
            type="Room",
            beds=1,
            bedrooms=1,
            price=500.0,
            building_name="Alpha Building",
            latitude=22.338,  # Close to campus1
            longitude=114.182,
            address="1 Alpha Road",
            geo_address="Kowloon Tong",
            flat_number="1A",
            floor_number="1",
            owner_name="Owner A",
            owner_contact="11111111"
        )
        self.acc2 = Accommodation.objects.create(
            accommodation_id=2,
            availability_start=today,
            availability_end=today + timedelta(days=30),
            type="Flat",
            beds=3,
            bedrooms=2,
            price=1500.0,
            building_name="Beta Building",
            latitude=22.340,  # Further from campus1
            longitude=114.185,
            address="2 Beta Street",
            geo_address="Lok Fu",
            flat_number="2B",
            floor_number="2",
            owner_name="Owner B",
            owner_contact="22222222"
        )
        self.acc3 = Accommodation.objects.create(
            accommodation_id=3,
            availability_start=today + timedelta(days=5),
            availability_end=today + timedelta(days=15),
            type="Room",
            beds=2,
            bedrooms=1,
            price=600.0,
            building_name="Gamma House",
            latitude=22.335,  # Very close to campus1
            longitude=114.179,
            address="3 Gamma Avenue",
            geo_address="Kowloon Tong",
            flat_number="3C",
            floor_number="3",
            owner_name="Owner C",
            owner_contact="33333333"
        )
        self.acc4 = Accommodation.objects.create(
            accommodation_id=4,
            availability_start=today - timedelta(days=5),
            availability_end=today + timedelta(days=5), # Ends soon
            type="Mini hall",
            beds=4,
            bedrooms=3,
            price=2000.0,
            building_name="Delta Tower",
            latitude=22.300,  # Far away
            longitude=114.170,
            address="4 Delta Drive",
            geo_address="Tsim Sha Tsui",
            flat_number="4D",
            floor_number="4",
            owner_name="Owner D",
            owner_contact="44444444"
        )

    def test_search_missing_campus_id(self):
        """
        Test search fails with 400 if campus_id is missing.
        """
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Campus ID is required", response.json()['errors'])

    def test_search_invalid_campus_id(self):
        """
        Test search fails with 400 if campus_id is invalid (e.g., 0, 6, non-numeric).
        """
        response = self.client.get(self.search_url, {'campus_id': 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Campus ID must be between 1-5", response.json()['errors'])

        response = self.client.get(self.search_url, {'campus_id': 6})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Assuming Campus IDs 1-5 exist, 6 doesn't.
        # The view code first checks range 1-5, then tries get(). So the error depends
        # on whether a Campus with ID 6 exists or not. Let's refine based on the code.
        # The code checks 1 <= campus_id <= 5 *first*.
        self.assertIn("Campus ID must be between 1-5", response.json()['errors'])

        response = self.client.get(self.search_url, {'campus_id': 'abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid campus ID", response.json()['errors']) # Error from int() failing

    def test_search_basic_with_campus_id_and_sorting(self):
        """
        Test basic search returns all accommodations sorted by distance to campus.
        Expected order based on coordinates: acc3 (closest), acc1, acc2, acc4 (farthest)
        """
        response = self.client.get(self.search_url, {'campus_id': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        self.assertEqual(len(results), 4)

        # Check order by ID (assuming distance calculation is correct)
        result_ids = [item['id'] for item in results] # Using 'id' from serializer
        expected_ids_order = [str(self.acc3.accommodation_id), str(self.acc1.accommodation_id), str(self.acc2.accommodation_id), str(self.acc4.accommodation_id)]
        self.assertEqual(result_ids, expected_ids_order)

        # Check distances are increasing (or equal)
        distances = [item['distance'] for item in results]
        self.assertTrue(all(distances[i] <= distances[i+1] for i in range(len(distances)-1)))
        self.assertIsNotNone(distances[0]) # Closest should have a non-null distance

    def test_search_filter_by_type(self):
        """
        Test filtering by accommodation type (e.g., type=1 for Room).
        """
        response = self.client.get(self.search_url, {'campus_id': 1, 'type': '1'}) # Type 1 = Room
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        self.assertEqual(len(results), 2)
        result_ids = sorted([item['id'] for item in results]) # Sort by ID for comparison consistency
        expected_ids = sorted([str(self.acc1.accommodation_id), str(self.acc3.accommodation_id)])
        self.assertEqual(result_ids, expected_ids)

    def test_search_filter_by_invalid_type(self):
        """ Test filtering by an invalid type value. """
        response = self.client.get(self.search_url, {'campus_id': 1, 'type': '5'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid type: use 1,2,3", response.json()['errors'])

    def test_search_filter_by_dates(self):
        """
        Test filtering by availability date range.
        Search for accommodations available between today+6 and today+14
        Only acc3 should match this narrow window.
        """
        start_date = (timezone.now().date() + timedelta(days=6)).strftime('%Y-%m-%d')
        end_date = (timezone.now().date() + timedelta(days=14)).strftime('%Y-%m-%d')
        response = self.client.get(self.search_url, {
            'campus_id': 1,
            'start_date': start_date,
            'end_date': end_date
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        self.assertEqual(len(results), 3)
        expected_ids_order = [str(self.acc3.accommodation_id), str(self.acc1.accommodation_id), str(self.acc2.accommodation_id)]
        result_ids = [item['id'] for item in results]
        self.assertEqual(result_ids, expected_ids_order)

    def test_search_filter_by_invalid_date_format(self):
        """ Test filtering with invalid date format. """
        response = self.client.get(self.search_url, {'campus_id': 1, 'start_date': '2023/01/01'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid date format. Use YYYY-MM-DD", response.json()['errors'])

    def test_search_filter_by_start_after_end_date(self):
        """ Test filtering with start date after end date. """
        start_date = (timezone.now().date() + timedelta(days=10)).strftime('%Y-%m-%d')
        end_date = (timezone.now().date() + timedelta(days=5)).strftime('%Y-%m-%d')
        response = self.client.get(self.search_url, {
            'campus_id': 1,
            'start_date': start_date,
            'end_date': end_date
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("End date must be after start date", response.json()['errors'])

    def test_search_filter_by_min_beds(self):
        """ Test filtering by minimum number of beds. """
        response = self.client.get(self.search_url, {'campus_id': 1, 'min_beds': 3})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        # Expect acc2 (3 beds) and acc4 (4 beds)
        self.assertEqual(len(results), 2)
        result_ids = sorted([item['id'] for item in results])
        expected_ids = sorted([str(self.acc2.accommodation_id), str(self.acc4.accommodation_id)])
        self.assertEqual(result_ids, expected_ids)

    def test_search_filter_by_min_bedrooms(self):
        """ Test filtering by minimum number of bedrooms. """
        response = self.client.get(self.search_url, {'campus_id': 1, 'min_bedrooms': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        # Expect acc2 (2 bedrooms) and acc4 (3 bedrooms)
        self.assertEqual(len(results), 2)
        result_ids = sorted([item['id'] for item in results])
        expected_ids = sorted([str(self.acc2.accommodation_id), str(self.acc4.accommodation_id)])
        self.assertEqual(result_ids, expected_ids)

    def test_search_filter_by_max_price(self):
        """ Test filtering by maximum price. """
        response = self.client.get(self.search_url, {'campus_id': 1, 'max_price': 700.0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        # Expect acc1 (500) and acc3 (600)
        self.assertEqual(len(results), 2)
        result_ids = sorted([item['id'] for item in results])
        expected_ids = sorted([str(self.acc1.accommodation_id), str(self.acc3.accommodation_id)])
        self.assertEqual(result_ids, expected_ids)

    def test_search_filter_by_invalid_numeric(self):
        """ Test filtering with invalid numeric parameter. """
        response = self.client.get(self.search_url, {'campus_id': 1, 'max_price': 'cheap'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid numeric parameter", response.json()['errors'])

        response = self.client.get(self.search_url, {'campus_id': 1, 'min_beds': 'many'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid numeric parameter", response.json()['errors'])

    def test_search_combined_filters(self):
        """
        Test combining multiple filters: type=Room, max_price=550
        Should only return acc1.
        """
        response = self.client.get(self.search_url, {
            'campus_id': 1,
            'type': '1',  # Room
            'max_price': 550.0
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], str(self.acc1.accommodation_id))

    def test_search_no_results(self):
        """
        Test a search query that yields no results.
        e.g., type=Flat, max_price=1000
        """
        response = self.client.get(self.search_url, {
            'campus_id': 1,
            'type': '2',  # Flat
            'max_price': 1000.0
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        self.assertEqual(len(results), 0)
        self.assertEqual(results, [])
