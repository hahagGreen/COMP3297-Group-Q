from django.shortcuts import render, HttpResponse, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from .models import Accommodation, Rating, Specialist, Student, Reservation, Campus
from .serializers import AccommodationSerializer, RatingSerializer
from datetime import datetime
import math
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import generics


# Create your views here.

def view_accommodations(request):
    accommodations = Accommodation.objects.all()
    if (request.method == 'POST'):
        # Handle form submission here
        queryId = request.POST.get('accommodation_id')
        accommodation = Accommodation.objects.get(accommodation_id=queryId)
        rate = Rating.objects.get(rating_id=queryId)
        return render(request, 'view.html', {'accommodation': accommodation, 'rate': rate})
    return render(request, 'demo.html', {'accommodations': accommodations})


# api for fetching accommodation details Epic3
@extend_schema(
    summary="View accommodation details",
    description="Fetch details of a specific accommodation for a given user.",
    parameters=[
        OpenApiParameter(name="accId", type=int, location=OpenApiParameter.QUERY, required=True, description="Accommodation ID to fetch details for"),
    ],
    methods=['GET'],
    responses={
        200: AccommodationSerializer,
        400: OpenApiResponse(description='Accommodation ID is required'),
        404: OpenApiResponse(description='User or Accommodation not found'),
    },
)
@extend_schema(
    summary="View accommodation details (POST)",
    description="Fetch details of a specific accommodation for a given user using POST method.",
    parameters=[
        OpenApiParameter(name="accId", type=int, location=OpenApiParameter.QUERY, required=True, description="Accommodation ID to fetch details for"),
    ],
    methods=['POST'],
    request={
        'application/x-www-form-urlencoded': {
            'schema': {
                'type': 'object',
                'properties': {
                    'userId': {'type': 'integer', 'description': 'ID of the user making the request'},
                },
                'required': ['userId'],
                'example': {
                    'userId': 1
                }
            }
        }
    },
    responses={
        200: AccommodationSerializer,
        400: OpenApiResponse(description='Accommodation ID is required'),
        404: OpenApiResponse(description='User or Accommodation not found'),
    },
)
@api_view(['GET', 'POST'])
def api_viewDetails(request):
    # Get user ID from request
    userId = request.POST.get('userId')
    try:
        # Check if user exists - no need to store the result if we're just validating
        Student.objects.get(user_id=userId)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    accommodation_id = request.GET.get('accId')
    if not accommodation_id:
        return JsonResponse({'error': 'Accommodation ID is required'}, status=400)

    try:
        accommodation = get_object_or_404(Accommodation, pk=accommodation_id)
        serializers = AccommodationSerializer(accommodation)

    except Accommodation.DoesNotExist:
        return JsonResponse({'error': 'Accommodation not found'}, status=404)
    return Response(serializers.data)


@extend_schema(
    summary="Search accommodations",
    description="Search for accommodations with various filters and sort by distance from campus.",
    parameters=[
        OpenApiParameter(
            name="type", 
            type=str, 
            description="Accommodation type (1=Room, 2=Flat, 3=Mini hall)", 
            enum=["1", "2", "3"]
        ),
        OpenApiParameter(
            name="start_date", 
            type=str, 
            description="Start date of availability period (YYYY-MM-DD)"
        ),
        OpenApiParameter(
            name="end_date", 
            type=str, 
            description="End date of availability period (YYYY-MM-DD)"
        ),
        OpenApiParameter(
            name="min_beds", 
            type=int, 
            description="Minimum number of beds required"
        ),
        OpenApiParameter(
            name="min_bedrooms", 
            type=int, 
            description="Minimum number of bedrooms required"
        ),
        OpenApiParameter(
            name="max_price", 
            type=float, 
            description="Maximum price per night in HKD"
        ),
        OpenApiParameter(
            name="campus_id", 
            type=int, 
            description="Campus ID for distance calculation", 
            required=True,
            enum=[1, 2, 3, 4, 5]
        ),
    ],
    responses={
        200: OpenApiResponse(response=AccommodationSerializer(many=True)),
        400: OpenApiResponse(description='Invalid parameters provided'),
    }
)
@api_view(['GET'])
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
    description="Add a rating for an accommodation and update the accommodation's average rating.",
    parameters=[
        OpenApiParameter(
            name="userId", 
            type=int, 
            description="ID of the student user submitting the rating",
            required=True,
            location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name="accId", 
            type=int, 
            description="ID of the accommodation being rated",
            required=True,
            location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name="rating", 
            type=int, 
            description="Rating value (0-5 stars)",
            required=True,
            location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name="date", 
            type=str, 
            description="Rating submission date (YYYY-MM-DD)",
            required=True,
            location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name="comment", 
            type=str, 
            description="Optional comment with the rating",
            required=False,
            location=OpenApiParameter.QUERY
        ),
    ],
    responses={
        200: OpenApiResponse(
            description='Rating updated successfully',
            response=RatingSerializer
        ),
        404: OpenApiResponse(description='User or Accommodation not found'),
    }
)
class ApiRateView(generics.GenericAPIView):
    """Add a rating for an accommodation via URL parameters."""
    serializer_class = RatingSerializer
    
    def post(self, request, *args, **kwargs):
        # Get parameters from URL query string instead of form data
        userId = request.GET.get('userId')
        try:
            user = Student.objects.get(user_id=userId)
        except Student.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        accommodation_id = request.GET.get('accId')
        newRating = request.GET.get('rating')
        date = request.GET.get('date')
        comment = request.GET.get('comment')  # Optional parameter
        
        rating = Rating.objects.create(
            user=user,
            accommodation=Accommodation.objects.get(accommodation_id=accommodation_id),
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