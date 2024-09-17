from django.core.management.base import BaseCommand
from core.services import fetch_disasters, check_disasters

class Command(BaseCommand):
    help = 'Fetch new disasters and check for affected alumni'

    def handle(self, *args, **options):
        fetch_disasters()
        check_disasters()
        self.stdout.write(self.style.SUCCESS('Successfully checked for disasters and notified if necessary'))