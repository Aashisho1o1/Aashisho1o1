# core/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
import core.views as views
from .views import AlumniViewSet, DisasterAlertViewSet, home

router = DefaultRouter()
router.register(r'alumni', AlumniViewSet, basename='alumni')
router.register(r'disaster-alerts', DisasterAlertViewSet, basename='disaster-alerts')

urlpatterns = [
    path('', include(router.urls)),  # Includes all router URLs
    path('home/', home, name='home'),  # Example home view
    path('disaster/<str:disaster_id>/', views.disaster_detail, name='disaster_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
