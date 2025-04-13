from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from .models import Accommodation, Reservation
import json
import requests

def api_view_active_reservations(request):
    """Epic 4.2 View Active Reservations"""
    if request.method == 'GET':
        # Fetch active reservations
        active_reservations = Reservation.objects.filter(status__in=['pending', 'confirmed'])
        reservations_list = []
        for reservation in active_reservations:
            reservations_list.append({
                'reservation_id': reservation.reservation_id,
                'user_id': reservation.user_id,
                'user_name': reservation.user.name,
                'user_email': reservation.user.email,
                'accommodation_id': reservation.accommodation_id, 
                'address': reservation.accommodation.address,
                'status': reservation.status,
            })
        return JsonResponse({'reservations': reservations_list})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def api_cancel_reservation(request):
    """Epic 4.1 Cancel Reservation"""
    if request.method == 'POST' or request.method == 'GET':
        reservation_id = request.POST.get("reservation_id") if request.method == 'POST' else request.GET.get("reservation_id")
        if reservation_id:
            try:
                # Update reservation status to 'canceled'
                updated_count = Reservation.objects.filter(
                    reservation_id=reservation_id
                ).update(status="canceled")
                
                if updated_count:
                    # Get the accommodation_id from the reservation
                    reservation = Reservation.objects.get(reservation_id=reservation_id)
                    accommodation_id = reservation.accommodation_id
                    
                    # Modify is_reserved in table Accommodation from 1 to 0.
                    Accommodation.objects.filter(
                        accommodation_id=accommodation_id
                    ).update(is_reserved=0)
                    return JsonResponse({'message': 'Reservation Canceled'})
                else:
                    return JsonResponse({'error': 'No matching reservation found'}, status=404)
            except Exception as e:
                print(f"Error cancelling reservation: {e}")
                return JsonResponse({'error': 'Error cancelling reservation'}, status=500)
        else:
            return JsonResponse({'error': 'Reservation ID not provided'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)