from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.validators import UniqueValidator

from TSTDriver import data
from account.models import Driver, Employee
from core.models import Leave, Holidays


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'date_joined']


class DriverSerializer(ModelSerializer):
    user = UserSerializer(many=False)
    added_by = serializers.CharField()

    class Meta:
        model = Driver
        fields = ['id', 'user', 'added_by']


class RecentLeaveSerializer(ModelSerializer):
    driver = UserSerializer(many=False)

    class Meta:
        model = Leave
        fields = "__all__"
        read_only_fields = ['driver', 'status_updated_by', 'leave_status']


class OverviewSerializer(Serializer):
    driver = serializers.IntegerField()


class DashboardSerializer(Serializer):
    overview = OverviewSerializer(many=False)
    new_drivers = DriverSerializer(many=True)
    recent_requests = RecentLeaveSerializer(many=True)


class DriverListSerializer(Serializer):
    driver = DriverSerializer(many=False)
    duty_hours = serializers.CharField()
    holidays = serializers.CharField()
    leave_requests = serializers.CharField()


class DriverDetailActivitiesSerializer(Serializer):
    date = serializers.CharField()
    duty_hours = serializers.IntegerField()
    holidays = serializers.IntegerField()


class DriverDetailSerializer(Serializer):
    driver = DriverSerializer(many=False)
    activities = DriverDetailActivitiesSerializer(many=True)


class DriverCreateSerializer(Serializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    phone_number = PhoneNumberField(required=True, validators=[UniqueValidator(queryset=Driver.objects.all())])
    first_name = serializers.CharField(max_length=200, required=True)
    last_name = serializers.CharField(max_length=200, required=True)
    birth_date = serializers.DateField(required=True)
    location = serializers.ChoiceField(choices=data.location)

    class Meta:
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'phone_number', 'birth_date', 'location')


class DriverUpdateSerializer(Serializer):
    email = serializers.EmailField(required=True)
    phone_number = PhoneNumberField(required=True)
    first_name = serializers.CharField(max_length=200, required=True)
    last_name = serializers.CharField(max_length=200, required=True)
    birth_date = serializers.DateField(required=True)
    location = serializers.ChoiceField(choices=data.location)

    class Meta:
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'birth_date', 'location')


class EmployeeUserSerializer(ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']


class EmployeeSerializer(ModelSerializer):
    user = EmployeeUserSerializer(many=False)
    phone_number = PhoneNumberField(
        required=True,
        validators=[UniqueValidator(queryset=Employee.objects.all())]
    )

    class Meta:
        model = Employee
        fields = '__all__'


class LeaveRequestSerializer(ModelSerializer):
    driver = UserSerializer(many=False)

    class Meta:
        model = Leave
        fields = '__all__'


class UpdateLeaveSerializer(ModelSerializer):
    class Meta:
        model = Leave
        fields = ['id', 'leave_status', 'special_leave_reason']


class CreateLeaveSerializer(ModelSerializer):
    class Meta:
        model = Leave
        fields = '__all__'


class EmployeeUserUpdateSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class UpdateEmployeeSerializer(ModelSerializer):
    user = EmployeeUserUpdateSerializer(many=False)

    class Meta:
        model = Employee
        fields = '__all__'


class LoggedInEmployeeSerializer(ModelSerializer):
    class Meta:
        model = Employee
        fields = ['can_add_driver', 'can_accept_leave_requests']


class EmployeeProfileSerializer(ModelSerializer):
    user = EmployeeUserUpdateSerializer(many=False)

    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ['can_add_driver', 'can_accept_leave_requests']


class UserForLeaveSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class DriverForLeaveSerializer(ModelSerializer):
    user = UserForLeaveSerializer(many=False)

    class Meta:
        model = Driver
        fields = ['user']


class SnapDataSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    code = serializers.CharField(max_length=100)
    value = serializers.IntegerField()


class EmployeeLeaves(Serializer):
    name = serializers.CharField(max_length=200)
    day = serializers.CharField(max_length=20)


class CalendarSerializer(Serializer):
    snapData = SnapDataSerializer(many=True)
    employeeLeaves = EmployeeLeaves(many=True)


class HolidaySerializer(ModelSerializer):
    class Meta:
        model = Holidays
        fields = '__all__'
