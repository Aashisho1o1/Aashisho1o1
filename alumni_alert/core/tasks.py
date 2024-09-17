# core/tasks.py

from celery import shared_task
from gdacs.api import GDACSAPIReader, GDACSAPIError
from django.utils import timezone
from django.contrib.gis.geos import Point
from .models import DisasterAlert
import logging

logger = logging.getLogger(__name__)

@shared_task
def fetch_latest_disasters(limit=10):
    client = GDACSAPIReader()
    try:
        events = client.latest_events(limit=limit)
        logger.debug(f"Fetched events: {events}")  # Add this line
        for event in events:
            logger.debug(f"Event Type: {type(event)} - Content: {event}")  # And this line
            # Rest of your code...
    except GDACSAPIError as e:
        logger.error(f"GDACSAPIError occurred: {e}")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")

def calculate_severity(event_type):
    severity_mapping = {
        "TC": 4,  # Critical
        "EQ": 3,  # High
        "FL": 2,  # Medium
        "VO": 1,  # Low
        "WF": 2,  # Medium
        "DR": 1,  # Low
    }
    return severity_mapping.get(event_type, 1)  # Default to Low if unknown
