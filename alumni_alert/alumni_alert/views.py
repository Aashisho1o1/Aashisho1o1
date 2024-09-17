# alumni_alert/views.py

from django.shortcuts import render
from .models import DisasterAlert

def alerts_list(request):
    alerts = DisasterAlert.objects.only('id', 'title', 'severity', 'description', 'location', 'created_at')
    return render(request, 'alerts/alerts_list.html', {'alerts': alerts})
