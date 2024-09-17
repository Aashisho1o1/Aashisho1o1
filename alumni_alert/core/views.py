# core/views.py

from django.shortcuts import render, get_object_or_404
from django.contrib.gis.measure import D
from django.core.serializers import serialize
from django.core.cache import cache
from rest_framework import viewsets, pagination, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from core import models
from .models import Alumni, DisasterAlert
from .serializers import AlumniSerializer, DisasterAlertSerializer
import logging
from django.shortcuts import render

# Configure logger
logger = logging.getLogger(__name__)

# ---------------------------
# Django REST Framework ViewSets
# ---------------------------

class StandardResultsSetPagination(pagination.PageNumberPagination):
    """
    Standard pagination settings.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000


class AlumniViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing alumni.
    """
    serializer_class = AlumniSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Optionally restricts the returned alumni by filtering against
        a `graduation_year` query parameter in the URL.
        """
        queryset = Alumni.objects.only('id', 'name', 'email', 'location', 'graduation_year').all()
        graduation_year = self.request.query_params.get('graduation_year', None)
        if graduation_year is not None:
            queryset = queryset.filter(graduation_year=graduation_year)
        return queryset


class DisasterAlertViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing disaster alerts.
    """
    queryset = DisasterAlert.objects.only(
        'id',
        'event_type',
        'event_id',
        'episode_id',
        'title',
        'severity',
        'description',
        'location',
        'created_at',
        'updated_at'
    ).all()
    serializer_class = DisasterAlertSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['severity', 'created_at']

    @action(detail=True, methods=['get'], url_path='affected-alumni')
    def affected_alumni(self, request, pk=None):
        """
        Retrieves alumni within a 100 km radius of the disaster location.
        """
        try:
            disaster = self.get_object()
            affected_alumni = Alumni.objects.filter(
                location__distance_lte=(disaster.location, D(km=100))
            )
            serializer = AlumniSerializer(affected_alumni, many=True)
            logger.info(f"Retrieved {affected_alumni.count()} affected alumni for disaster: {disaster.title}")
            return Response(serializer.data)
        except DisasterAlert.DoesNotExist:
            logger.error(f"DisasterAlert with pk={pk} does not exist.")
            return Response({'error': 'DisasterAlert not found.'}, status=404)
        except Exception as e:
            logger.error(f"Error retrieving affected alumni: {e}")
            return Response({'error': 'An error occurred while retrieving affected alumni.'}, status=500)

# ---------------------------
# Standard Django Views
# ---------------------------

def home(request):
    """
    Renders the home page with counts and GeoJSON data for alumni and disasters.
    Utilizes caching to optimize performance.
    """
    # Retrieve and cache alumni count
    alumni_count = cache.get('alumni_count')
    if alumni_count is None:
        alumni_count = Alumni.objects.count()
        cache.set('alumni_count', alumni_count, 300)  # Cache for 5 minutes

    # Retrieve and cache disaster count
    disaster_count = cache.get('disaster_count')
    if disaster_count is None:
        disaster_count = DisasterAlert.objects.count()
        cache.set('disaster_count', disaster_count, 300)  # Cache for 5 minutes

    # Retrieve and cache alumni GeoJSON data
    alumni_geojson = cache.get('alumni_geojson')
    if alumni_geojson is None:
        alumni_queryset = Alumni.objects.only('id', 'name', 'email', 'location', 'graduation_year')
        alumni_geojson = serialize(
            'geojson',
            alumni_queryset,
            geometry_field='location',
            fields=('name', 'email', 'graduation_year')
        )
        cache.set('alumni_geojson', alumni_geojson, 300)  # Cache for 5 minutes

    # Retrieve and cache disaster GeoJSON data
    disaster_geojson = cache.get('disaster_geojson')
    if disaster_geojson is None:
        disaster_queryset = DisasterAlert.objects.only(
            'id',
            'event_type',
            'event_id',
            'episode_id',
            'title',
            'severity',
            'description',
            'location'
        )
        disaster_geojson = serialize(
            'geojson',
            disaster_queryset,
            geometry_field='location',
            fields=('event_type', 'event_id', 'episode_id', 'title', 'severity', 'description')
        )
        cache.set('disaster_geojson', disaster_geojson, 300)  # Cache for 5 minutes

    context = {
        'alumni_count': alumni_count,
        'disaster_count': disaster_count,
        'alumni_geojson': alumni_geojson,
        'disaster_geojson': disaster_geojson,
    }

    return render(request, 'core/home.html', context)


def disaster_detail(request, disaster_id):
    """
    Renders the disaster detail page with the disaster information and nearby alumni.
    """
    disaster = get_object_or_404(DisasterAlert, event_id=disaster_id)
    nearby_alumni = Alumni.objects.filter(
        location__distance_lte=(disaster.location, D(km=50))
    ).annotate(
        distance=models.functions.Distance('location', disaster.location)
    ).order_by('distance')

    context = {
        'disaster': disaster,
        'nearby_alumni': nearby_alumni,
    }

    return render(request, 'core/disaster_detail.html', context)




def index(request):
    return render(request, 'core/index.html')

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    return render(request, 'core/contact.html')
