from rest_framework import serializers
from .models import Accommodation
import math

class AccommodationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='accommodation_id')
    startDate = serializers.DateField(source='availability_start')
    endDate = serializers.DateField(source='availability_end')
    numOfBeds = serializers.IntegerField(source='beds')
    numOfBedrooms = serializers.IntegerField(source='bedrooms')
    is_reserved = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Accommodation
        fields = [
            'id', 'startDate', 'endDate', 'type', 'numOfBeds',
            'numOfBedrooms', 'price', 'address',
            'latitude', 'longitude', 'is_reserved', 'distance'
        ]

    def get_is_reserved(self, obj):
        return "yes" if obj.is_reserved else "no"

    def get_distance(self, obj):
        campus = self.context.get('campus')
        if campus:
            lon1, lat1, lon2, lat2 = map(math.radians, [obj.longitude, obj.latitude, campus.longitude, campus.latitude])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            return 6371 * 2 * math.asin(math.sqrt(a))  # Earth radius in km
        return None