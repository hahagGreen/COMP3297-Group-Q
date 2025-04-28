from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from .models import (
    Campus, Student, Specialist, Accommodation, AccommodationOffering,
    Reservation, Rating
)


class ReservationAPITests(APITestCase):
    def setUp(self):
        # 校区
        self.campus_hku = Campus.objects.create(
            name='HKU', latitude=22.283, longitude=114.137
        )
        self.campus_cuhk = Campus.objects.create(
            name='CUHK', latitude=22.419, longitude=114.210
        )
        self.campus_hkust = Campus.objects.create(
            name='HKUST', latitude=22.336, longitude=114.265
        )
        # 用户
        self.student_hku = Student.objects.create(
            name="Alice", email="alice@example.com", password="test", campus=self.campus_hku
        )
        self.student_cuhk = Student.objects.create(
            name="Bob", email="bob@example.com", password="test", campus=self.campus_cuhk
        )
        self.student_hkust = Student.objects.create(
            name="Charlie", email="charlie@example.com", password="test", campus=self.campus_hkust
        )
        self.specialist_hku = Specialist.objects.create(
            name="SpecHKU", email="sphku@example.com", password="test", campus=self.campus_hku, contact="123"
        )
        self.specialist_cuhk = Specialist.objects.create(
            name="SpecCUHK", email="spcuhk@example.com", password="test", campus=self.campus_cuhk, contact="456"
        )
        self.specialist_hkust = Specialist.objects.create(
            name="SpecHKUST", email="sphkust@example.com", password="test", campus=self.campus_hkust, contact="789"
        )
        # 房源
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
        # 挂载到两个校区
        self.offering_hku = AccommodationOffering.objects.create(
            accommodation=self.accommodation,
            campus=self.campus_hku,
            specialist=self.specialist_hku
        )
        self.offering_cuhk = AccommodationOffering.objects.create(
            accommodation=self.accommodation,
            campus=self.campus_cuhk,
            specialist=self.specialist_cuhk
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.student_hku)
    def test_list_reservations_success(self):
        reservation = Reservation.objects.create(
            user=self.student_hku,
            accommodation=self.accommodation,
            status=Reservation.PENDING
        )
        url = reverse('reservation_list_api', args=[self.student_hku.user_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['reservation_id'], reservation.reservation_id)

    def test_list_reservations_no_campus(self):
        student = Student.objects.create(
            name="NoCampus", email="no-campus@example.com", password="test", campus=None
        )
        url = reverse('reservation_list_api', args=[student.user_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("User is not associated with any campus.", resp.data.get("error", ""))

    def test_list_reservations_other_campus(self):
        """不同校区看不到其他校区的预约"""
        Reservation.objects.create(
            user=self.student_hkust,
            accommodation=self.accommodation,
            status=Reservation.PENDING
        )
        url = reverse('reservation_list_api', args=[self.student_hkust.user_id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)

    def test_add_reservation_success(self):
        url = reverse('add_reservation_api', args=[self.student_hku.user_id, self.accommodation.accommodation_id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.accommodation.refresh_from_db()
        self.assertTrue(self.accommodation.is_reserved)

    def test_add_reservation_wrong_campus(self):
        url = reverse('add_reservation_api', args=[self.student_hkust.user_id, self.accommodation.accommodation_id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You can only reserve accommodations offered to your campus.", resp.data.get("error", ""))

    def test_add_reservation_already_reserved(self):
        self.accommodation.is_reserved = True
        self.accommodation.save()
        url = reverse('add_reservation_api', args=[self.student_hku.user_id, self.accommodation.accommodation_id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already reserved", resp.data.get("error", ""))

    def test_add_reservation_pending_exists(self):
        Reservation.objects.create(
            user=self.student_hku,
            accommodation=self.accommodation,
            status=Reservation.PENDING
        )
        url = reverse('add_reservation_api', args=[self.student_hku.user_id, self.accommodation.accommodation_id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pending reservation", resp.data.get("error", ""))

    def test_add_reservation_time_overlap(self):
        acc2 = Accommodation.objects.create(
            availability_start=timezone.now().date(),
            availability_end=timezone.now().date(),
            type="Flat",
            beds=2,
            bedrooms=1,
            price=1200.0,
            building_name="Other Building",
            latitude=22.283,
            longitude=114.137,
            address="124 Queen's Road",
            geo_address="Central, HK",
            room_number=None,
            flat_number="B",
            floor_number="3",
            owner_name="Mr. Lee",
            owner_contact="87654321",
            is_reserved=False
        )
        AccommodationOffering.objects.create(
            accommodation=acc2,
            campus=self.campus_hku,
            specialist=self.specialist_hku
        )
        Reservation.objects.create(
            user=self.student_hku,
            accommodation=acc2,
            status=Reservation.CONFIRMED
        )
        url = reverse('add_reservation_api', args=[self.student_hku.user_id, self.accommodation.accommodation_id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("overlap", resp.data.get("error", ""))

    def test_cancel_reservation_success(self):
        reservation = Reservation.objects.create(
            user=self.student_hku,
            accommodation=self.accommodation,
            status=Reservation.PENDING
        )
        self.accommodation.is_reserved = True
        self.accommodation.save()
        url = reverse('cancel_reservation_api', args=[self.student_hku.user_id, reservation.reservation_id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.accommodation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.CANCELED)
        self.assertFalse(self.accommodation.is_reserved)

    def test_cancel_reservation_wrong_campus(self):
        reservation = Reservation.objects.create(
            user=self.student_hkust,
            accommodation=self.accommodation,
            status=Reservation.PENDING
        )
        url = reverse('cancel_reservation_api', args=[self.student_hkust.user_id, reservation.reservation_id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("for your campus", resp.data.get("error", ""))

    def test_cancel_reservation_status_error(self):
        reservation = Reservation.objects.create(
            user=self.student_hku,
            accommodation=self.accommodation,
            status=Reservation.COMPLETED
        )
        url = reverse('cancel_reservation_api', args=[self.student_hku.user_id, reservation.reservation_id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot cancel", resp.data.get("error", ""))

    def test_rate_reservation_completed(self):
        reservation = Reservation.objects.create(
            user=self.student_hku,
            accommodation=self.accommodation,
            status=Reservation.COMPLETED
        )
        url = reverse('rate_reservation', args=[reservation.reservation_id])
        resp = self.client.post(url, {"rating": 5}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["rating"], 5)
        self.assertEqual(resp.data["accommodation_rating"]["count"], 1)
        self.assertEqual(resp.data["accommodation_rating"]["average"], 5)

    def test_rate_reservation_not_completed(self):
        reservation = Reservation.objects.create(
            user=self.student_hku,
            accommodation=self.accommodation,
            status=Reservation.PENDING
        )
        url = reverse('rate_reservation', args=[reservation.reservation_id])
        resp = self.client.post(url, {"rating": 3}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Can only rate completed reservations", resp.data.get("error", ""))

    def test_rate_reservation_invalid_value(self):
        reservation = Reservation.objects.create(
            user=self.student_hku,
            accommodation=self.accommodation,
            status=Reservation.COMPLETED
        )
        url = reverse('rate_reservation', args=[reservation.reservation_id])
        resp = self.client.post(url, {"rating": 8}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Rating must be between 0 and 5", resp.data.get("error", ""))

    def test_rate_reservation_update(self):
        reservation = Reservation.objects.create(
            user=self.student_hku,
            accommodation=self.accommodation,
            status=Reservation.COMPLETED
        )
        url = reverse('rate_reservation', args=[reservation.reservation_id])
        resp = self.client.post(url, {"rating": 4}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["rating"], 4)
        resp2 = self.client.post(url, {"rating": 5}, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertEqual(resp2.data["rating"], 5)
        self.assertTrue(abs(resp2.data["accommodation_rating"]["average"] - 5.0) < 1e-5)

    def test_add_reservation_no_campus(self):
        student = Student.objects.create(
            name="NoCampus", email="no-campus2@example.com", password="test", campus=None
        )
        url = reverse('add_reservation_api', args=[student.user_id, self.accommodation.accommodation_id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("User is not associated with any campus.", resp.data.get("error", ""))

    def test_cancel_reservation_no_campus(self):
        student = Student.objects.create(
            name="NoCampus", email="no-campus3@example.com", password="test", campus=None
        )
        reservation = Reservation.objects.create(
            user=student,
            accommodation=self.accommodation,
            status=Reservation.PENDING
        )
        url = reverse('cancel_reservation_api', args=[student.user_id, reservation.reservation_id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("User is not associated with any campus.", resp.data.get("error", ""))

    # 补充：权限测试——学生不能做specialist的动作
    def test_student_cannot_cancel_others_reservation(self):
        # 假设student_hku试图取消student_cuhk的预约
        reservation = Reservation.objects.create(
            user=self.student_cuhk,
            accommodation=self.accommodation,
            status=Reservation.PENDING
        )
        url = reverse('cancel_reservation_api', args=[self.student_hku.user_id, reservation.reservation_id])
        resp = self.client.post(url)
        # 应该是404或者403
        self.assertIn(resp.status_code, [403, 404])

    # 还可以继续扩展更多边界和异常测试


# 补充说明：如需覆盖specialist权限、房源管理等API，可参考类似写法扩展
