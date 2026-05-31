from rest_framework import serializers
from .models import Monitor, CheckResult, Incident
from django.conf import settings


class MonitorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Monitor
        fields = '__all__'
        read_only_fields = ['owner', 'created_at']

    def validate(self, attrs):
        request = self.context.get('request')

        # only check on creation, not on update
        if self.instance is None:
            active_count = Monitor.objects.filter(
                owner=request.user,
                is_active=True
            ).count()

            if active_count >= settings.MAX_ACTIVE_MONITORS_PER_USER:
                raise serializers.ValidationError(
                    f"Free tier limit: maximum {settings.MAX_ACTIVE_MONITORS_PER_USER} active monitors per user."
                )

        return attrs

class CheckResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = CheckResult
        fields = "__all__"

class IncidentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Incident
        fields = "__all__"
