from rest_framework import serializers
from .models import Alumni, DisasterAlert

class AlumniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumni
        fields = [
            'id',
            'name',
            'email',
            'country',
            'city',
            'graduation_year',
            'location'
        ]

class DisasterAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisasterAlert
        fields = [
            'id',
            'title',
            'description',
            'location',
            'severity',
            'created_at',
            'updated_at'
        ]