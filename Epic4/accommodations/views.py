from django.shortcuts import render
from django.http import JsonResponse
from .models import Accommodation, Rating, Campus
from .serializers import AccommodationSerializer
from datetime import datetime
import math

def view_accommodations(request):
    accommodations = Accommodation.objects.all()
    if(request.method == 'POST'):
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
            serializer = AccommodationSerializer(accommodation)
            return JsonResponse(serializer.data)
        except Accommodation.DoesNotExist:
            return JsonResponse({'error': 'Accommodation not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


def api_search(request):
    """
    Search accommodations with filters and sort by distance from campus
    Query Parameters:
    - type: 1=Room, 2=Flat, 3=Mini hall
    - start_date: YYYY-MM-DD
    - end_date: YYYY-MM-DD
    - min_beds: integer
    - min_bedrooms: integer
    - max_price: decimal
    - campus_id: 1-5
    """
    params = request.GET
    errors = []
    campus = None
    queryset = Accommodation.objects.all()

    # Validate campus ID (1-5)
    if 'campus_id' in params:
        try:
            campus_id = int(params['campus_id'])
            if 1 <= campus_id <= 5:
                campus = Campus.objects.get(campus_id=campus_id)
            else:
                errors.append("Campus ID must be between 1-5")
        except (ValueError, Campus.DoesNotExist):
            errors.append("Invalid campus ID")
    else:
        errors.append("Campus ID is required")
            
    # Type filter
    type_mapping = {'1': 'Room', '2': 'Flat', '3': 'Mini hall'}
    if 'type' in params:
        accommodation_type = type_mapping.get(params['type'])
        if accommodation_type:
            queryset = queryset.filter(type=accommodation_type)
        else:
            errors.append("Invalid type: use 1,2,3")

    # Date range filter
    try:
        start_date = None
        end_date = None
        
        if 'start_date' in params:
            start_date = datetime.strptime(params['start_date'], '%Y-%m-%d').date()
        if 'end_date' in params:
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d').date()
            
        if start_date and end_date and start_date > end_date:
            errors.append("End date must be after start date")
            
        if start_date:
            queryset = queryset.filter(availability_end__gte=start_date)
        if end_date:
            queryset = queryset.filter(availability_start__lte=end_date)
    except ValueError:
        errors.append("Invalid date format. Use YYYY-MM-DD")

    # Numeric filters
    try:
        if 'min_beds' in params:
            queryset = queryset.filter(beds__gte=int(params['min_beds']))
        if 'min_bedrooms' in params:
            queryset = queryset.filter(bedrooms__gte=int(params['min_bedrooms']))
        if 'max_price' in params:
            queryset = queryset.filter(price__lte=float(params['max_price']))
    except ValueError:
        errors.append("Invalid numeric parameter")

    # Return errors if any
    if errors:
        return JsonResponse({'errors': errors}, status=400)

    # Serialize with distance calculation
    serializer = AccommodationSerializer(
        queryset,
        many=True,
        context={'campus': campus}  # Pass campus for distance calculation
    )
    data = serializer.data

    # Sort by distance if valid campus
    if campus:
        data = sorted(
            data,
            key=lambda x: x['distance'] if x['distance'] is not None else math.inf
        )

    return JsonResponse(data, safe=False)