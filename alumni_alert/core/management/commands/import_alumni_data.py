# core/management/commands/import_alumni_data.py

import csv
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point
from django.db import transaction
from core.models import Alumni

class Command(BaseCommand):
    help = 'Import alumni data from a CSV file into PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='The path to the CSV file to import'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to create per batch'
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        batch_size = options['batch_size']
        required_headers = {'Name', 'Email', 'City', 'Country', 'Latitude', 'Longitude', 'Graduation Year'}

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                csv_headers = set(reader.fieldnames)

                # Validate CSV headers
                missing_headers = required_headers - csv_headers
                if missing_headers:
                    raise CommandError(f'Missing required CSV headers: {", ".join(missing_headers)}')

                alumni_to_create = []
                alumni_created = 0
                alumni_skipped = 0

                self.stdout.write(self.style.NOTICE('Starting import...'))

                for row_num, row in enumerate(reader, start=2):  # Starting at 2 to account for header
                    try:
                        email = row['Email'].strip()
                        # Skip if alumni already exists
                        if Alumni.objects.filter(email=email).exists():
                            self.stdout.write(self.style.WARNING(f"Row {row_num}: Alumni with email {email} already exists. Skipping."))
                            alumni_skipped += 1
                            continue

                        # Parse and validate latitude and longitude
                        latitude = row.get('Latitude')
                        longitude = row.get('Longitude')

                        if not latitude or not longitude:
                            self.stderr.write(self.style.ERROR(f"Row {row_num}: Missing Latitude or Longitude. Skipping."))
                            alumni_skipped += 1
                            continue

                        try:
                            latitude = float(latitude)
                            longitude = float(longitude)
                            location = Point(longitude, latitude)  # Point(lon, lat)
                        except ValueError:
                            self.stderr.write(self.style.ERROR(f"Row {row_num}: Invalid Latitude or Longitude. Skipping."))
                            alumni_skipped += 1
                            continue

                        # Parse graduation year
                        graduation_year = row.get('Graduation Year')
                        if not graduation_year:
                            self.stderr.write(self.style.ERROR(f"Row {row_num}: Missing Graduation Year. Skipping."))
                            alumni_skipped += 1
                            continue

                        try:
                            graduation_year = int(graduation_year)
                        except ValueError:
                            self.stderr.write(self.style.ERROR(f"Row {row_num}: Invalid Graduation Year. Skipping."))
                            alumni_skipped += 1
                            continue

                        alumni = Alumni(
                            name=row['Name'].strip(),
                            email=email,
                            city=row.get('City', '').strip(),
                            country=row.get('Country', '').strip(),
                            location=location,
                            graduation_year=graduation_year
                        )
                        alumni_to_create.append(alumni)

                        # Bulk create in batches
                        if len(alumni_to_create) >= batch_size:
                            with transaction.atomic():
                                Alumni.objects.bulk_create(alumni_to_create, ignore_conflicts=True)
                            alumni_created += len(alumni_to_create)
                            self.stdout.write(self.style.SUCCESS(f"Imported {alumni_created} alumni so far..."))
                            alumni_to_create = []

                    except KeyError as e:
                        self.stderr.write(self.style.ERROR(f"Row {row_num}: Missing field {e}. Skipping."))
                        alumni_skipped += 1
                        continue
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Row {row_num}: Unexpected error: {e}. Skipping."))
                        alumni_skipped += 1
                        continue

                # Create any remaining alumni
                if alumni_to_create:
                    with transaction.atomic():
                        Alumni.objects.bulk_create(alumni_to_create, ignore_conflicts=True)
                    alumni_created += len(alumni_to_create)

                self.stdout.write(self.style.SUCCESS(f"Successfully imported {alumni_created} alumni records."))
                if alumni_skipped:
                    self.stdout.write(self.style.WARNING(f"Skipped {alumni_skipped} records due to errors or duplicates."))

        except FileNotFoundError:
            raise CommandError(f"File '{csv_file_path}' does not exist.")
        except PermissionError:
            raise CommandError(f"Permission denied for file '{csv_file_path}'.")
        except csv.Error as e:
            raise CommandError(f"CSV parsing error: {e}")
        except Exception as e:
            raise CommandError(f"An unexpected error occurred: {e}")
