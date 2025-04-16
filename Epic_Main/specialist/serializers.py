from rest_framework import serializers
from .models import Accommodation, Reservation, Student, Specialist

class AccommodationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accommodation
        fields = '__all__'

class ReservationSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = '__all__'

    def get_username(self, obj):
        # Fetch the related User instance using user_id
        user = Student.objects.get(user_id=obj.user_id)
        return user.name
    
    def get_email(self, obj):
        # Fetch the related User instance using user_id
        user = Student.objects.get(user_id=obj.user_id)
        return user.email
    
    def get_address(self, obj):
        # Fetch the related Accommodation instance using accommodation_id
        accommodation = Accommodation.objects.get(accommodation_id=obj.accommodation_id)
        return accommodation.address
