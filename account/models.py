from django.contrib.auth.models import User
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from TSTDriver import data


class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver')
    phone_number = PhoneNumberField(unique=True)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(blank=True, null=True)
    isVerified = models.BooleanField(blank=False, default=False)
    counter = models.IntegerField(default=0, blank=False)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='added_by')
    location = models.CharField(max_length=200, choices=data.location, default='Worms')

    def __str__(self):
        return self.user.get_username()


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee')
    phone_number = PhoneNumberField()
    can_add_driver = models.BooleanField(default=False, blank=True)
    can_accept_leave_requests = models.BooleanField(default=False, blank=True)
    location = models.CharField(max_length=200, choices=data.location, default='Worms')

    def __str__(self):
        return self.user.username
