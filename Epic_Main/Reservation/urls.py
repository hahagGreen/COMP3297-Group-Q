# reservations/urls.py
from django.urls import path
from .views import (
    ReservationListView, 
    AddReservationView, 
    CancelReservationView,
    reservation_list_view,
    add_reservation_view,
    rate_reservation
)

urlpatterns = [
    # API endpoints
    path('list/<int:user_id>/', ReservationListView.as_view(), name='reservation_list_api'),
    path('add/<int:user_id>/<int:accommodation_id>/', AddReservationView.as_view(), name='add_reservation_api'),
    path('cancel/<int:user_id>/<int:reservation_id>/', CancelReservationView.as_view(), name='cancel_reservation_api'),
    path('rate/<int:reservation_id>/', rate_reservation, name='rate_reservation'),
    
    # Web views
    path('view/list/<int:user_id>/', reservation_list_view, name='reservation_list'),
    path('view/add/', add_reservation_view, name='add_reservation'),
]