from django.contrib.auth.models import User
from django.db import models


# Create your models here.
from TSTDriver import data


class Leave(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='driver_leave')
    leave_type = models.CharField(max_length=200, choices=data.leave_type, default='Urlaub')
    special_leave_reason = models.CharField(max_length=200, blank=True, choices=data.special_leave_reason, default='Eheschließung eines Kindes')
    from_date = models.DateField()
    to_date = models.DateField()
    message = models.TextField(blank=True)
    leave_status = models.CharField(max_length=100, choices=data.leave_status, default='Pending')
    status_updated_by = models.ForeignKey(User, to_field='username', on_delete=models.SET_NULL, null=True, blank=True, related_name='status_updater')
    status_updated_date = models.DateField(auto_now=True)

    def __str__(self):
        return self.driver.username


class Activities(models.Model):
    driver = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_activity')
    activity_type = models.CharField(max_length=100, choices=data.activity_type, default="Duty")
    start_date = models.DateField()
    start_time = models.TimeField()
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    status = models.CharField(max_length=100, choices=data.activity_status, blank=True, default="Running")

    def __str__(self):
        return self.driver.username

    class Meta:
        verbose_name_plural = 'Activities'
        verbose_name = 'Activity'


class SleepMode(models.Model):
    activity = models.ForeignKey(Activities, on_delete=models.CASCADE, related_name='sleep_activity')
    sleep_start_date = models.DateField()
    sleep_start = models.TimeField()
    sleep_end_date = models.DateField(blank=True, null=True)
    sleep_end = models.TimeField(blank=True, null=True)

    def __str__(self):
        return str(self.activity.id)


class Trips(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='driver_trip')
    start_date = models.DateField()
    end_date = models.DateField()
    duty_start_time = models.TimeField()
    duty_end_time = models.TimeField()
    duty_hour = models.CharField(max_length=20)
    sleep_start_time = models.TimeField()
    sleep_end_time = models.TimeField()
    sleep_hour = models.CharField(max_length=20)

    def __str__(self):
        return self.driver.username

    class Meta:
        verbose_name = 'Trip'
        verbose_name_plural = 'Trips'


class Holidays(models.Model):
    date = models.DateField(unique=True)
    title = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Holiday'
        verbose_name_plural = 'Holidays'

    def __str__(self):
        return self.title.title()
