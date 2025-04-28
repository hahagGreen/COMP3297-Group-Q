from django.urls import path
from . import views

urlpatterns = [
    path('view/', views.view_accommodations, name='view_accommodations'),
    path('api_view', views.ApiViewDetails.as_view(), name='api_view'),
    path('api_search', views.ApiSearchView.as_view(), name='api_search'),
    path('api_rate', views.ApiRateView.as_view(), name='api_rate'),
]

