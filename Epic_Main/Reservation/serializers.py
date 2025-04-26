# reservations/serializers.py
from rest_framework import serializers
from .models import Reservation, Rating


class ReservationRatingSerializer(serializers.ModelSerializer):
    """Serializer for Rating model in the Reservation app (renamed to avoid collision)"""
    class Meta:
        model = Rating
        fields = ['rating_id', 'rating', 'date']
        read_only_fields = ['rating_id', 'date']


class ReservationSerializer(serializers.ModelSerializer):
    rating = ReservationRatingSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ('user', 'accommodation', 'status', 'rating')


class CreateReservationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    accommodation_id = serializers.IntegerField()