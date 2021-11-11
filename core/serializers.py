from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import Leave, Activities, SleepMode, Trips


class LeaveSerializer(ModelSerializer):
    class Meta:
        model = Leave
        fields = "__all__"
        read_only_fields = ['driver', 'status_updated_by', 'leave_status']


class ActivitySerializer(ModelSerializer):
    class Meta:
        model = Activities
        fields = ['driver', 'activity_type', 'start_date', 'start_time', 'status']
        read_only_fields = ['driver', 'activity_type', 'status']


class SleepSerializer(ModelSerializer):
    class Meta:
        model = SleepMode
        fields = ['sleep_start_date', 'sleep_start', 'sleep_end_date', 'sleep_end']


class CurrentUserActivitySerializer(ModelSerializer):
    sleep = SleepSerializer(many=True)

    class Meta:
        model = Activities
        fields = '__all__'


class SleepStartSerializer(ModelSerializer):
    class Meta:
        model = SleepMode
        fields = '__all__'
        read_only_fields = ['activity', 'sleep_end', 'sleep_end_date']


class SleepEndSerializer(ModelSerializer):
    class Meta:
        model = SleepMode
        fields = '__all__'
        read_only_fields = ['activity', 'sleep_start', 'sleep_start_date']


class TripSerializer(serializers.Serializer):
    driver = serializers.IntegerField(required=False)
    trip_start_date = serializers.DateField(required=True)
    trip_start_time = serializers.TimeField(required=True)
    trip_sleep_hour_start = serializers.TimeField(required=False)
    trip_sleep_hour_end = serializers.TimeField(required=False)
    trip_end_date = serializers.DateField(required=True)
    trip_end_time = serializers.TimeField(required=True)
    total_duty_hour = serializers.CharField(required=True, max_length=10)
    total_sleep_hour = serializers.CharField(required=True, max_length=10)
    sleep_data = SleepSerializer(many=True)

    class Meta:
        fields = ['driver', 'trip_start_date', 'trip_start_time', 'trip_sleep_hour_start', 'trip_sleep_hour_end',
                  'trip_end_date', 'trip_end_time', 'total_duty_hour', 'total_sleep_hour', 'sleep_data']
        read_only_fields = ['driver']


class TripCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trips
        fields = "__all__"
        read_only_fields = ['driver']


class ActivityStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activities
        fields = ['end_date', 'end_time', 'status']
