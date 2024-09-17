# core/models.py

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point

class Alumni(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    location = models.PointField(geography=True, srid=4326)  # Using geography for spherical calculations
    graduation_year = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['location']),
        ]
        ordering = ['name']  # Define default ordering here

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.location:
            self.location = Point(0.0, 0.0)  # Default to (0, 0) if no location is provided
        super().save(*args, **kwargs)

    @property
    def latitude(self):
        return self.location.y if self.location else None

    @property
    def longitude(self):
        return self.location.x if self.location else None

class DisasterAlert(models.Model):
    EVENT_TYPES = [
        ('TC', 'Tropical Cyclones'),
        ('EQ', 'Earthquakes'),
        ('FL', 'Floods'),
        ('VO', 'Volcanoes'),
        ('WF', 'Wild Fires'),
        ('DR', 'Droughts'),
    ]

    SEVERITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]

    event_type = models.CharField(max_length=2, choices=EVENT_TYPES)
    event_id = models.CharField(max_length=20)
    episode_id = models.CharField(max_length=10, blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.PointField(geography=True, srid=4326)  # Retain geography=True for spherical calculations
    severity = models.IntegerField(choices=SEVERITY_CHOICES)
    source_format = models.CharField(max_length=10, default='xml')  # To store format like 'xml', 'geojson', etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('event_type', 'event_id', 'episode_id')
        indexes = [
            models.Index(fields=['location']),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.title} - Severity: {self.get_severity_display()}"

    @property
    def latitude(self):
        return self.location.y if self.location else None

    @property
    def longitude(self):
        return self.location.x if self.location else None
