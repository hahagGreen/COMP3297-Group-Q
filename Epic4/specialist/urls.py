from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_accommodations, name='add_accommodations'),
    path('api_add/', views.api_add, name='api_add'),
    path('api_active', views.api_view_active_reservations, name='api_active'),
    path('api_cancel', views.api_cancel_reservation, name='api_cancel'),
    path('api_modify', views.api_modify, name='api_modify'),
]
