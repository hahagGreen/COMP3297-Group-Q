# accommodations/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_accommodations, name='search_accommodations'),
    path('api/search/', views.search_accommodations_api, name='search_accommodations_api'),
]