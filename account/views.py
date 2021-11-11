import base64
import math
from datetime import datetime

import pyotp
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from twilio.rest import Client as TwilioClient

from account.models import Driver
from account.serializer import RegisterSerializer, UpdateProfileSerializer, DriverSerializer, PhoneSerializer, \
    OTPSerializer, ChangePasswordSerializer, ProfileSerializer, ProfileDetailSerializer
from core.models import Trips, Leave


class RegisterAPIView(viewsets.GenericViewSet,
                      mixins.CreateModelMixin, ):
    serializer_class = RegisterSerializer
    queryset = User.objects.all()
    authentication_classes = []
    permission_classes = []


class UpdateAPIView(viewsets.GenericViewSet,
                    mixins.CreateModelMixin):
    serializer_class = UpdateProfileSerializer
    queryset = User.objects.all()

    def create(self, request, *args, **kwargs):
        user = User.objects.get(id=self.request.user.id)
        serializer = self.serializer_class(instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        driver = Driver.objects.get(user=self.request.user)
        driver_serializer = DriverSerializer(instance=driver, data=request.data)
        driver_serializer.is_valid(raise_exception=True)
        driver_serializer.save()
        return Response(serializer.data)


class generateKey:
    @staticmethod
    def returnValue(phone):
        return str(phone) + str(datetime.date(datetime.now()))


class OTPAPIView(viewsets.GenericViewSet,
                 mixins.CreateModelMixin):
    serializer_class = PhoneSerializer
    queryset = Driver.objects.all()
    permission_classes = []
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                driver = Driver.objects.get(phone_number=serializer.data['phone_number'])
                driver.counter += 1  # Update Counter At every Call
                driver.save()
                keygen = generateKey()
                key = base64.b32encode(keygen.returnValue(driver).encode())  # Key is generated
                OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created
                twilio_client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                try:
                    twilio_client.messages.create(to=driver.phone_number, from_=settings.TWILIO_NUMBER,
                                                  body='Enter ' + OTP.at(driver.counter) + ' to verify account')
                except:
                    return Response({'error': 'Unable to send otp to this number'}, status.HTTP_400_BAD_REQUEST)
                # Using Multi-Threading send the OTP Using Messaging Services like Twilio or Fast2sms
                return Response({"OTP": OTP.at(driver.counter)}, status=200)  # Just for demonstration
            except:
                return Response({'error': 'No driver found with this phone number'}, status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerifyAPIView(viewsets.GenericViewSet,
                       mixins.CreateModelMixin):
    serializer_class = OTPSerializer
    queryset = Driver.objects.all()
    authentication_classes = []
    permission_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                driver = Driver.objects.get(phone_number=request.data['phone_number'])
                keygen = generateKey()
                key = base64.b32encode(keygen.returnValue(driver).encode())  # Generating Key
                OTP = pyotp.HOTP(key)  # HOTP Model
                if OTP.verify(request.data["otp"], driver.counter):  # Verifying the OTP
                    driver.isVerified = True
                    driver.save()
                    user = User.objects.get(id=driver.user.id)
                    user.is_active = True
                    user.save()
                    serializer.data['status'] = 'Authorized'

                    return Response({'status': 'Authorized'}, status.HTTP_200_OK)
                else:
                    return Response({'status': 'Invalid OTP'}, status.HTTP_400_BAD_REQUEST)
            except ObjectDoesNotExist:
                return Response(
                    self.serializer_class({'status': "Driver doesn't exist with this phone number"}, many=False).data,
                    status=status.HTTP_404_NOT_FOUND)  # False Call
        else:
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class ChangePassword(viewsets.GenericViewSet,
                     mixins.CreateModelMixin):
    serializer_class = ChangePasswordSerializer
    queryset = User.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            if serializer.data['new_password'] != serializer.data['confirm_new_password']:
                return Response({"error": "Password fields didn't match."}, status.HTTP_400_BAD_REQUEST)
            auth = authenticate(request, username=self.request.user.username,
                                password=serializer.data['current_password'])
            if auth:
                user = User.objects.get(username=self.request.user.username)
                user.set_password(serializer.data['new_password'])
                user.save()
                response = {'status': 'Password is changed'}
                code = status.HTTP_200_OK
            else:
                response = {'error': 'Incorrect current password'}
                code = status.HTTP_400_BAD_REQUEST
            return Response(response, code)
        else:
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


class ProfileAPIView(viewsets.GenericViewSet,
                     mixins.ListModelMixin):
    serializer_class = ProfileSerializer
    queryset = User.objects.all()

    def list(self, request, *args, **kwargs):
        current_site = get_current_site(request)
        user = User.objects.get(id=self.request.user.id)
        driver = Driver.objects.get(user=self.request.user)
        trips = Trips.objects.filter(driver=user)
        hours = 0
        minutes = 0
        for trip in trips:
            d = trip.duty_hour.split(':')
            hours += int(d[0])
            minutes += int(d[1])
        hours += math.floor(minutes / 60)
        minutes = math.floor(minutes % 60)
        leave = Leave.objects.filter(driver=self.request.user).count()
        return Response(self.serializer_class(
            {'first_name': user.first_name, 'last_name': user.last_name, 'username': user.get_username(),
             'total_trips': trips.count(),
             'duty_hour': str(hours) + ':' + str(minutes), 'total_leave': leave}, many=False).data, status.HTTP_200_OK)


class ProfileDetails(viewsets.GenericViewSet,
                     mixins.ListModelMixin):
    serializer_class = ProfileDetailSerializer
    queryset = User.objects.all()

    def list(self, request, *args, **kwargs):
        a = User.objects.get(id=self.request.user.id)
        driver = Driver.objects.get(user=a)
        user = {'first_name': a.first_name, 'last_name': a.last_name, 'email': a.email,
                'phone_number': driver.phone_number, 'bio': driver.bio,
                'birth_date': driver.birth_date}
        return Response(self.serializer_class(user, many=False).data, status.HTTP_200_OK)
