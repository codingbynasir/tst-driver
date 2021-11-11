from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from account.models import Driver


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    phone_number = PhoneNumberField(write_only=True)
    first_name = serializers.CharField(max_length=200, required=True)
    last_name = serializers.CharField(max_length=200, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'phone_number')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        Driver.objects.create(user=user, phone_number=validated_data['phone_number'])
        return user


class UpdateProfileSerializer(serializers.ModelSerializer):
    bio = serializers.CharField(max_length=255)
    birth_date = serializers.DateField()
    phone_number = PhoneNumberField(required=True)
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'bio', 'birth_date', 'phone_number')


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['user', 'bio', 'birth_date', 'phone_number']
        read_only_fields = ['user']


class PhoneSerializer(serializers.Serializer):
    phone_number = PhoneNumberField(required=True)

    class Meta:
        fields = ['phone_number']


class OTPSerializer(serializers.Serializer):
    phone_number = PhoneNumberField(required=True, write_only=True)
    otp = serializers.CharField(required=True, write_only=True)
    status = serializers.CharField(max_length=200, read_only=True)

    class Meta:
        fields = ['phone_number', 'otp', 'status']
        read_only_fields = ['status']


class ChangePasswordSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(max_length=200, required=True)
    new_password = serializers.CharField(max_length=200, required=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(max_length=200, required=True)

    class Meta:
        model = User
        fields = ['current_password', 'new_password', 'confirm_new_password']


class ProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField()
    total_trips = serializers.IntegerField()
    duty_hour = serializers.CharField()
    total_leave = serializers.CharField()

    class Meta:
        fields = ['first_name', 'last_name', 'username', 'total_trips', 'duty_hour', 'total_leave']


class ProfileDetailSerializer(serializers.Serializer):
    phone_number = PhoneNumberField(required=True)
    birth_date = serializers.DateField(required=True)
    bio = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'birth_date', 'bio']
