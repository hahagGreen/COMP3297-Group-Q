from datetime import datetime
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import Reservation, Accommodation, Student, Rating
from .serializers import ReservationSerializer, CreateReservationSerializer
from django.core.mail import send_mail


class ReservationListView(APIView):
    @extend_schema(
        summary="List user reservations",
        description="Retrieves a list of all reservations associated with the given user ID.",
        responses={
            200: OpenApiResponse(response=ReservationSerializer(many=True),
                                 description='List of reservations retrieved successfully.'),
            404: OpenApiResponse(description='User not found.'),
        }
    )
    def get(self, request, user_id):
        user = get_object_or_404(Student, pk=user_id)
        reservations = Reservation.objects.filter(user=user)
        serializer = ReservationSerializer(reservations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddReservationView(APIView):
    serializer_class = ReservationSerializer

    @extend_schema(
        summary="Create a new reservation",
        description="""Creates a new reservation for the specified user and accommodation ID.
        Checks for availability, existing pending reservations, and time overlaps.
        Marks the accommodation as reserved upon successful creation.
        Returns the created reservation details or an error message.""",
        responses={
            201: OpenApiResponse(response=ReservationSerializer, description='Reservation created successfully.'),
            400: OpenApiResponse(
                description='Bad Request (e.g., accommodation already reserved, pending reservation exists, time overlap).'),
            404: OpenApiResponse(description='User or Accommodation not found.'),
        }
    )
    def post(self, request, user_id, accommodation_id):
        user = get_object_or_404(Student, pk=user_id)
        accommodation = get_object_or_404(Accommodation, pk=accommodation_id)

        if accommodation.is_reserved:
            return Response({"error": "The selected accommodation is already reserved."},
                            status=status.HTTP_400_BAD_REQUEST)

        if Reservation.objects.filter(user=user, status=Reservation.PENDING).exists():
            return Response({"error": "You already have a pending reservation."}, status=status.HTTP_400_BAD_REQUEST)

        user_reservations = Reservation.objects.filter(user=user)
        for res in user_reservations:
            if not ((accommodation.availability_end < res.accommodation.availability_start or
                    accommodation.availability_start > res.accommodation.availability_end)) and (res.status == "Confirmed" or res.status == "Pending"):
                return Response({"error": "Reservation time overlaps with an existing reservation."},
                                status=status.HTTP_400_BAD_REQUEST)

        reservation = Reservation.objects.create(
            user=user,
            accommodation=accommodation,
            status=Reservation.PENDING
        )

        accommodation.is_reserved = True
        accommodation.save()

        send_mail(
            'Reservation Confirmation',
            f"""
            Dear {user.name},

            Your reservation has been successfully created and is now pending approval.

            Reservation Details:
            - Reservation ID: {reservation.reservation_id}
            - Accommodation: {accommodation.type} at {accommodation.address}
            - Status: Pending

            We will notify you once your reservation has been reviewed by a specialist.

            Thank you for using UniHaven!
            """,
            'noreplyhku0@gmail.com',
            [user.email],
            fail_silently=False,
        )

        serializer = ReservationSerializer(reservation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CancelReservationView(APIView):
    serializer_class = ReservationSerializer
    
    @extend_schema(
        summary="Cancel an existing reservation",
        description="""Cancels the reservation specified by the reservation ID for the given user ID.
        Marks the associated accommodation as available again.
        Returns a success message upon cancellation.""",
        responses={
            200: OpenApiResponse(description='Reservation canceled successfully.'),
            404: OpenApiResponse(description='Reservation or User not found.'),
        }
    )
    def post(self, request, user_id, reservation_id):
        reservation = get_object_or_404(Reservation, pk=reservation_id, user__user_id=user_id)

        if reservation.status not in [Reservation.PENDING, Reservation.CONFIRMED]:
            return Response({"error": "Cannot cancel a completed or already canceled reservation."},
                            status=status.HTTP_400_BAD_REQUEST)

        accommodation = reservation.accommodation
        accommodation.is_reserved = False
        accommodation.save()

        reservation.status = Reservation.CANCELED
        reservation.save()

        send_mail(
            'Reservation Cancellation Confirmation',
            f"""
            Dear {reservation.user.name},

            Your reservation has been cancelled successfully.

            Reservation Details:
            - Reservation ID: {reservation.reservation_id}
            - Accommodation: {accommodation.type} at {accommodation.address}
            - Status: Pending

            Thank you for using UniHaven!
            """,
            'noreplyhku0@gmail.com',
            [reservation.user.email],
            fail_silently=False,
        )

        return Response({"message": "Reservation canceled successfully."}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Rate a completed reservation",
    description="Add or update rating for a completed reservation.",
    request={
        'application/json': {
            'schema': {
                'type': 'object',
                'properties': {
                    'rating': {'type': 'integer', 'description': 'Rating value from 0 to 5', 'minimum': 0, 'maximum': 5},
                },
                'required': ['rating'],
                'example': {
                    'rating': 4
                }
            }
        }
    },
    responses={
        200: OpenApiResponse(
            description='Rating updated successfully',
            response={
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'rating': {'type': 'integer'},
                    'accommodation_rating': {
                        'type': 'object',
                        'properties': {
                            'average': {'type': 'number'},
                            'count': {'type': 'integer'}
                        }
                    }
                },
                'example': {
                    'message': 'Rating updated successfully',
                    'rating': 4,
                    'accommodation_rating': {
                        'average': 4.5,
                        'count': 2
                    }
                }
            }
        ),
        400: OpenApiResponse(description='Invalid rating or reservation not completed'),
        404: OpenApiResponse(description='Reservation not found'),
    }
)
def rate_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id)

    if reservation.status != Reservation.COMPLETED:
        return Response({"error": "Can only rate completed reservations"}, status=status.HTTP_400_BAD_REQUEST)

    rating_value = request.data.get('rating')
    if not 0 <= rating_value <= 5:
        return Response({"error": "Rating must be between 0 and 5"}, status=status.HTTP_400_BAD_REQUEST)

    rating, created = Rating.objects.get_or_create(
        reservation=reservation,
        defaults={'rating': rating_value}
    )

    if not created:
        old_rating = rating.rating
        rating.rating = rating_value
        rating.save()

        # Update accommodation average rating
        accommodation = reservation.accommodation
        total_rating = accommodation.average_rating * accommodation.rating_count
        total_rating = total_rating - old_rating + rating_value
        accommodation.average_rating = total_rating / accommodation.rating_count
        accommodation.save()
    else:
        # Update accommodation average rating
        accommodation = reservation.accommodation
        total_rating = accommodation.average_rating * accommodation.rating_count
        accommodation.rating_count += 1
        accommodation.average_rating = (total_rating + rating_value) / accommodation.rating_count
        accommodation.save()

    return Response({
        "message": "Rating updated successfully",
        "rating": rating_value,
        "accommodation_rating": {
            "average": accommodation.average_rating,
            "count": accommodation.rating_count
        }
    })


# Web views
def reservation_list_view(request, user_id):
    user = get_object_or_404(Student, pk=user_id)
    reservations = Reservation.objects.filter(user=user)
    return render(request, 'reservation_list.html', {
        'reservations': reservations,
        'user': user
    })


def add_reservation_view(request):
    return render(request, 'add_reservation.html')