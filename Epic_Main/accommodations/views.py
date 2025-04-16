from django.shortcuts import render, HttpResponse, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from .models import Accommodation,Rating, Specialist,Student, Reservation
from .serializers import AccommodationSerializer, RatingSerializer
from datetime import datetime
import math
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

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

# api for fetching accommodation details Epic3
@extend_schema(
    summary="View accommodation details",
    description="Fetch details of a specific accommodation for a given user.",
    methods=['GET', 'POST'],
    parameters=[
        OpenApiParameter(name="accId", type=int, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter(name="userId", type=int, required=True),
    ],
    responses={
        200: AccommodationSerializer,
        400: OpenApiResponse(description='Accommodation ID is required'),
        404: OpenApiResponse(description='User or Accommodation not found'),
    }
)
@api_view(['GET','POST'])
def api_viewDetails(request):
    userId = request.POST.get('userId')
    try:
        user = Student.objects.get(user_id=userId)
        # print(user.name)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    accommodation_id = request.GET.get('accId')
    if not accommodation_id:
        return JsonResponse({'error': 'Accommodation ID is required'}, status=400)
        
    try:
        accommodation = get_object_or_404(Accommodation,pk=accommodation_id)
        serializers = AccommodationSerializer(accommodation)
        
    except Accommodation.DoesNotExist:
        return JsonResponse({'error': 'Accommodation not found'}, status=404)
    return Response(serializers.data)

@extend_schema(
    summary="Search accommodations",
    description="Search for accommodations with various filters like type, dates, beds, price, etc.",
    parameters=[
        OpenApiParameter(name="type", type=str, description="1=Room, 2=Flat, 3=Mini hall"),
        OpenApiParameter(name="start_date", type=str, description="YYYY-MM-DD"),
        OpenApiParameter(name="end_date", type=str, description="YYYY-MM-DD"),
        OpenApiParameter(name="min_beds", type=int, description="Minimum number of beds"),
        OpenApiParameter(name="min_bedrooms", type=int, description="Minimum number of bedrooms"),
        OpenApiParameter(name="max_price", type=float, description="Maximum price"),
        OpenApiParameter(name="campus_id", type=int, description="Campus ID (1-5) for distance calculation"),
    ],
    responses={
        200: OpenApiResponse(response=AccommodationSerializer(many=True)),
        400: OpenApiResponse(description='Invalid parameters provided'),
    }
)
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

# api for updating rating details Epic5
@extend_schema(
    summary="Rate accommodation",
    description="Add or update rating for an accommodation after a completed reservation.",
    parameters=[
        OpenApiParameter(name="userId", type=int, required=True),
        OpenApiParameter(name="reservId", type=int, required=True),
        OpenApiParameter(name="accId", type=int, required=True),
        OpenApiParameter(name="rating", type=int, required=True),
        OpenApiParameter(name="date", type=str, required=True),
    ],
    responses={
        200: OpenApiResponse(description='Rating updated successfully'),
        404: OpenApiResponse(description='User or Accommodation not found'),
    }
)
@api_view(['POST'])
def api_rate(request):   
    userId = request.POST.get('userId')
    try:
        user = Student.objects.get(user_id=userId)
        print(user.name)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)  
    accommodation_id = request.POST.get('accId')
    newRating = request.POST.get('rating')
    date = request.POST.get('date')
    comment = None
    if(request.POST.get('comment')):
        comment = request.POST.get('comment')
    rating = Rating.objects.create(
            user = Student.objects.get(user_id=userId),
            accommodation = Accommodation.objects.get(accommodation_id=accommodation_id),
            rating=newRating,
            date=date,
            comment=comment
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


