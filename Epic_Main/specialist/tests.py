from django.urls import reverse
from rest_framework.test import APITestCase, APIClient, APIRequestFactory
from rest_framework import status
from django.utils import timezone
from .models import (
    Campus, Student, Specialist, Accommodation, AccommodationOffering,
    Reservation, Rating
)
from .views import ApiAddView, ApiCancelReservationView, ApiModifyReservationView

class SpecialistAddTest(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.userId = 1
        self.specialist = Specialist.objects.create(
            name = 'Test Specialist',
            email = "test@test.com",
            password = "testpassword",
            contact = "1234567890",
            campus = Campus.objects.create(
                name = 'Test Campus',
                latitude = 0.0,
                longitude = 0.0
            )
        )
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
        self.startDate = "2025-01-01"
        self.endDate = "2025-12-31"
        self.type = 'Mini hall'
        self.price = 100.0
        self.beds = 2
        self.bedrooms = 1
        self.buildingName = "Test Building"
        self.ownerName = "Test Owner"
        self.ownerContact = "1234567890"
        self.address = "University of Hong Kong, Pokfulam, Hong Kong"
        self.roomNumber = "101"
        self.flatNumber = "1A"
        self.floorNumber = "1"
        

    def test_add_accommodation(self):
            """
            Test the add accommodation API endpoint successfully operated
            """
            url = f"/specialist/api_add?userId={self.userId}&startDate={self.startDate}&endDate={self.endDate}&type={self.type}&price={self.price}&beds={self.beds}&bedrooms={self.bedrooms}&buildingName={self.buildingName}&ownerName={self.ownerName}&ownerContact={self.ownerContact}&address={self.address}&roomNumber={self.roomNumber}&flatNumber={self.flatNumber}&floorNumber={self.floorNumber}"
            request = self.factory.post(url)
            response = ApiAddView.as_view()(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['availability_start'], self.startDate)
            self.assertEqual(response.data['availability_end'], self.endDate)
            self.assertEqual(response.data['type'], self.type)
            self.assertEqual(response.data['price'], self.price)
            self.assertEqual(response.data['beds'], self.beds)
            self.assertEqual(response.data['bedrooms'], self.bedrooms)
            self.assertEqual(response.data['building_name'], self.buildingName)
            self.assertEqual(response.data['owner_name'], self.ownerName)
            self.assertEqual(response.data['owner_contact'], self.ownerContact)
            self.assertEqual(response.data['address'], self.address)
            self.assertEqual(response.data['room_number'], self.roomNumber)
            self.assertEqual(response.data['flat_number'], self.flatNumber)
            self.assertEqual(response.data['floor_number'], self.floorNumber)

    def test_accommodation_geoAddress(self):
        """
        Test the function for fetching geo address
        """
        url = f"/specialist/api_add?userId={self.userId}&startDate={self.startDate}&endDate={self.endDate}&type={self.type}&price={self.price}&beds={self.beds}&bedrooms={self.bedrooms}&buildingName={self.buildingName}&ownerName={self.ownerName}&ownerContact={self.ownerContact}&address={self.address}&roomNumber={self.roomNumber}&flatNumber={self.flatNumber}&floorNumber={self.floorNumber}"
        request = self.factory.post(url)
        response = ApiAddView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['geo_address'], '3195213838T20050430')
        self.assertEqual(response.data['latitude'], 22.26353)
        self.assertEqual(response.data['longitude'], 114.13527)
    
    def test_specialistNotFound(self):
        """
        Test the add accommodation API endpoint when the specialist is not found
        """
        url = f"/specialist/api_add?userId=999&startDate={self.startDate}&endDate={self.endDate}&type={self.type}&price={self.price}&beds={self.beds}&bedrooms={self.bedrooms}&buildingName={self.buildingName}&ownerName={self.ownerName}&ownerContact={self.ownerContact}&address={self.address}&roomNumber={self.roomNumber}&flatNumber={self.flatNumber}&floorNumber={self.floorNumber}"
        request = self.factory.post(url)
        response = ApiAddView.as_view()(request)
        self.assertEqual(response.status_code, 404)  
