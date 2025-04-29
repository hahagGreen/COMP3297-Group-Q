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

class AccommodationSearchTests(APITestCase):
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
class AccommodationRatingTests(APITestCase):
    def setup(self):
        pass
