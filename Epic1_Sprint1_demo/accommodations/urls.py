# accommodations/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_accommodations, name='search_accommodations'),
    path('api/search/', views.Search_Accommodations_API.as_view(), name='search_accommodations_api'),
]