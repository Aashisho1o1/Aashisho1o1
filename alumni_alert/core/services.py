import requests
import xml.etree.ElementTree as ET
from django.template.loader import render_to_string
from django.contrib.gis.measure import D
#from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.gis.geos import Point
from .models import Alumni, DisasterAlert
from .tasks import send_consolidated_report_task
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import logging

# Configure logger
logger = logging.getLogger(__name__)

def fetch_disasters():
    url = "https://www.gdacs.org/xml/rss.xml"
    try:
        response = requests.get(url)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        logger.info("Successfully fetched disaster data from GDACS.")
    except requests.RequestException as e:
        logger.error(f"Error fetching disaster data: {e}")
        return

    for item in root.findall('.//item'):
        try:
            title = item.find('title').text
            description = item.find('description').text
            lat = float(item.find('geo:lat', {'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#'}).text)
            lon = float(item.find('geo:long', {'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#'}).text)

            if not DisasterAlert.objects.filter(title=title, location=Point(lon, lat)).exists():
                DisasterAlert.objects.create(
                    title=title,
                    description=description,
                    location=Point(lon, lat),
                    severity=calculate_severity(title),
                    created_at=timezone.now()
                )
                logger.info(f"Created new DisasterAlert: {title}")
            else:
                logger.debug(f"DisasterAlert already exists: {title}")
        except AttributeError as e:
            logger.warning(f"Missing expected XML tags in item: {e}")
        except ValueError as e:
            logger.warning(f"Invalid latitude or longitude values: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing disaster item: {e}")


def calculate_severity(title):
    if "Red Alert" in title:
        return 4  # Critical
    elif "Orange Alert" in title:
        return 3  # High
    elif "Green Alert" in title:
        return 1  # Low
    else:
        return 2  # Medium

def check_disasters():
    """
    Fetches recent disasters and sends a consolidated report of impacted alumni.
    """
    # Define the time frame for recent disasters, e.g., last 24 hours
    time_threshold = timezone.now() - timezone.timedelta(days=1)
    recent_disasters = DisasterAlert.objects.filter(created_at__gte=time_threshold)
    
    for disaster in recent_disasters:
        impacted_alumni = find_affected_alumni(disaster)
        
        # If there are impacted alumni, send a consolidated report
        if impacted_alumni.exists():
            # Pass disaster.id and a list of alumni IDs to the task
            send_consolidated_report_task.delay(disaster.id, list(impacted_alumni.values_list('id', flat=True)))

"""
def find_affected_alumni(disaster):
    radius = D(km=100)
    return Alumni.objects.only('id', 'name', 'email', 'location', 'graduation_year').filter(
        location__distance_lte=(Point(disaster.longitude, disaster.latitude), radius)
    )
"""

def find_affected_alumni(disaster):
    radius = D(km=100)
    return Alumni.objects.only('id', 'name', 'email', 'location', 'graduation_year').filter(
        location__distance_lte=(disaster.location, radius)
    )

def validate_emails(email_list):
    """
    Validates a list of email addresses.
    
    :param email_list: List of email addresses to validate
    :return: List of valid email addresses
    """
    valid_emails = []
    for email in email_list:
        try:
            validate_email(email)
            valid_emails.append(email)
        except ValidationError:
            logger.error(f"Invalid email address detected and skipped: {email}")
            # Optionally, collect invalid emails for further processing
    return valid_emails

def send_consolidated_report(disaster, impacted_alumni):
    """
    Sends a consolidated report of impacted alumni for a specific disaster to the admin and supervisor.
    
    :param disaster: DisasterAlert instance
    :param impacted_alumni: QuerySet of Alumni instances affected by the disaster
    """
    subject = f"Disaster Alert Report: {disaster.title} - {disaster.get_severity_display()}"
    
    # Render the HTML email template
    message = render_to_string('core/disaster_report_email.html', {
        'disaster': disaster,
        'impacted_alumni': impacted_alumni,
    })
    
    # Define recipients
    recipients = [settings.ADMIN_EMAIL, settings.SUPERVISOR_EMAIL]

    # Send the consolidated report asynchronously
    send_consolidated_report_task.delay(subject, message, recipients)

