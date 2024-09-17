# test_gdacs.py

from gdacs.api import GDACSAPIReader, GDACSAPIError

client = GDACSAPIReader()
try:
    events = client.latest_events(limit=5)
    print(f"Type of events: {type(events)}")
    print(f"Events: {events}")
    for event in events:
        print(f"Type of event: {type(event)} - Content: {event}")
except GDACSAPIError as e:
    print(f"GDACSAPIError occurred: {e}")
except Exception as e:
    print(f"Unexpected error occurred: {e}")
