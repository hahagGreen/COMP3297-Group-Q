from django.urls import path
from . import views

urlpatterns = [
    path('view/', views.view_accommodations,name='view_accommodations'),
    path('api_rate', views.api_rate,name='api_rate'),
]
