from django.shortcuts import render, HttpResponse, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from .models import Accommodation,Rating, User, Reservation
from .serializers import AccommodationSerializer, RatingSerializer, ReservationSerializer
# Create your views here.

# api for updating rating details Epic5
@api_view(['POST'])
def api_rate(request):   
    userId = request.POST.get('userId')
    try:
        user = User.objects.get(user_id=userId)
        print(user.name)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)  
    reservation_id = request.POST.get('reservId')
    accommodation_id = request.POST.get('accId')
    newRating = request.POST.get('rating')
    date = request.POST.get('date')
    rating = Rating.objects.create(
            reservation=Reservation.objects.get(reservation_id=reservation_id),
            rating=newRating,
            date=date
        )
    try:
        accommodation = Accommodation.objects.get(accommodation_id=accommodation_id)
        count = accommodation.rating_count
        accommodation.rating_count = count + 1
        accommodation.average_rating = (accommodation.average_rating * count + int(newRating)) / (count + 1)
        accommodation.save()
    except Accommodation.DoesNotExist:
        return JsonResponse({'error': 'Accommodation not found'}, status=404)
    serializers_rating = RatingSerializer(rating)
    serializers_accommodation = AccommodationSerializer(accommodation)
    serializer = [serializers_rating.data, serializers_accommodation.data]
    content = {
        'status': 'success',
        'message': 'Rating updated successfully',
        'data': serializer
    }
    return Response(content)
