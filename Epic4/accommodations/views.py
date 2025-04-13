from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from .models import Accommodation,Rating
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

def api_view(request):
    if request.method == 'GET':
        accommodation_id = request.GET.get('id')
        if not accommodation_id:
            return JsonResponse({'error': 'Accommodation ID is required'}, status=400)
        
        try:
            accommodation = Accommodation.objects.get(accommodation_id=accommodation_id)
            accommodation_details = {
                'id': accommodation_id,
                'startDate': accommodation.availability_start,
                'endDate': accommodation.availability_end,
                'type': accommodation.type,
                'numOfBeds': accommodation.beds,
                'numOfBedrooms': accommodation.bedrooms,
                'price': accommodation.price,
                'address': accommodation.address,
                'geo_address': accommodation.geo_address,
                'latitude': accommodation.latitude,
                'longitude': accommodation.longitude,
                'is_reserved': "yes" if accommodation.is_reserved else "no",
            }
            return JsonResponse(accommodation_details)
        except Accommodation.DoesNotExist:
            return JsonResponse({'error': 'Accommodation not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method '}, status=405)

