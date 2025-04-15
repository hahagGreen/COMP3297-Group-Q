from django.urls import path
from . import views

urlpatterns = [
    path('view/', views.view_accommodations,name='view_accommodations'),
    path('api_view', views.api_view, name='api_view'),
    path('api_search', views.api_search, name='api_search'),
]
