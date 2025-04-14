from django.urls import path
from . import views

urlpatterns = [
    path('view/', views.view_accommodations,name='view_accommodations'),
    path('api_view', views.api_viewDetails,name='api_view'),
]

