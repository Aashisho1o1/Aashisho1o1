# core/admin.py

from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin  # Updated import
from .models import Alumni, DisasterAlert

@admin.register(Alumni)
class AlumniAdmin(LeafletGeoAdmin):
    list_display = ('name', 'email', 'city', 'country', 'graduation_year', 'latitude', 'longitude')
    readonly_fields = ('latitude', 'longitude')
    # Optionally, you can customize the map widget further if needed

@admin.register(DisasterAlert)
class DisasterAlertAdmin(LeafletGeoAdmin):
    list_display = ('title', 'severity', 'created_at', 'latitude', 'longitude')
    readonly_fields = ('latitude', 'longitude')
