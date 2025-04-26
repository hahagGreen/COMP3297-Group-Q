from rest_framework import serializers
from .models import Accommodation, Reservation, Student, Specialist
from drf_spectacular.utils import extend_schema_field

class SpecialistAccommodationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accommodation
        fields = '__all__'

class SpecialistReservationSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = '__all__'

    @extend_schema_field(serializers.CharField())
    def get_username(self, obj):
        # Fetch the related User instance using user_id
        user = Student.objects.get(user_id=obj.user_id)
        return user.name
    
    @extend_schema_field(serializers.EmailField())
    def get_email(self, obj):
        # Fetch the related User instance using user_id
        user = Student.objects.get(user_id=obj.user_id)
        return user.email
    
    @extend_schema_field(serializers.CharField())
    def get_address(self, obj):
        # Fetch the related Accommodation instance using accommodation_id
        accommodation = Accommodation.objects.get(accommodation_id=obj.accommodation_id)
        return accommodation.address
