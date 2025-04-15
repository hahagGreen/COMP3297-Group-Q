from django.urls import path
from . import views

urlpatterns = [
    path('api_rate', views.api_rate,name='api_rate'),
]
