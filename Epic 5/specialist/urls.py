from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_accommodations,name='add_accommodations'),
     path('api_add/', views.api_add,name='api_add'),
     path('api_edit/', views.api_edit,name='api_edit'),
]
