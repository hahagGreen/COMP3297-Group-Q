from django.shortcuts import render, HttpResponse, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from .models import Accommodation,Rating, User
from .serializers import AccommodationSerializer
# Create your views here.

def view_accommodations(request):
    accommodations = Accommodation.objects.all()
    if(request.method == 'POST'):
        # Handle form submission here
        queryId = request.POST.get('accommodation_id')
        accommodation = Accommodation.objects.get(accommodation_id = queryId)
        rate = Rating.objects.get(rating_id = queryId)
        return render(request, 'view.html', {'accommodation': accommodation, 'rate': rate})
    return render(request, 'demo.html', {'accommodations': accommodations})

# api for fetching accommodation details
@api_view(['GET','POST'])
def api_view(request):
    userId = request.POST.get('userId')
    try:
        user = User.objects.get(user_id=userId)
        print(user.name)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    accommodation_id = request.GET.get('accId')
    if not accommodation_id:
        return JsonResponse({'error': 'Accommodation ID is required'}, status=400)
        
    try:
        accommodation = get_object_or_404(Accommodation,pk=accommodation_id)
        serializers = AccommodationSerializer(accommodation)
        return Response(serializers.data)
    except Accommodation.DoesNotExist:
        return JsonResponse({'error': 'Accommodation not found'}, status=404)


