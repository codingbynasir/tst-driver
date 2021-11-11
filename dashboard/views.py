import calendar
from datetime import datetime

import coreapi
from django.contrib.auth.models import User
from rest_framework import mixins, status
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from account.models import Driver, Employee
from core.models import Leave, Trips, Holidays
from dashboard.custom_permission import IsSuperUser
from dashboard.serializers import DriverSerializer, RecentLeaveSerializer, DashboardSerializer, DriverListSerializer, \
    DriverCreateSerializer, EmployeeSerializer, LeaveRequestSerializer, UpdateLeaveSerializer, UpdateEmployeeSerializer, \
    DriverUpdateSerializer, LoggedInEmployeeSerializer, EmployeeProfileSerializer, CreateLeaveSerializer, \
    DriverForLeaveSerializer, CalendarSerializer, HolidaySerializer, DriverDetailSerializer


class DashboardAPIView(GenericViewSet,
                       mixins.ListModelMixin):
    serializer_class = DashboardSerializer
    queryset = Driver.objects.all()

    def list(self, request, *args, **kwargs):
        driver = Driver.objects.count()
        overview = {'driver': driver}
        drivers = DriverSerializer(Driver.objects.all().order_by("-user__date_joined")[:5], many=True)
        leave = RecentLeaveSerializer(Leave.objects.filter(leave_status='Pending').order_by('-status_updated_date')[:5],
                                      many=True)
        context = {
            'overview': overview,
            'new_drivers': drivers.data,
            'recent_requests': leave.data
        }
        return Response(context, status=status.HTTP_200_OK)


class DriversAPIView(GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.UpdateModelMixin):
    queryset = Driver.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return DriverCreateSerializer
        if self.action in ['update', 'partial_update']:
            return DriverUpdateSerializer
        if self.action == 'retrieve':
            return DriverDetailSerializer
        else:
            return DriverListSerializer

    def create(self, request, *args, **kwargs):
        staff = Employee.objects.get(user=self.request.user)
        if staff.can_add_driver is False:
            return Response({'detail': 'You are not authorized to add driver'}, status.HTTP_401_UNAUTHORIZED)
        serializer = DriverCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.create(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            first_name=serializer.validated_data['first_name'],
            last_name=serializer.validated_data['last_name']
        )
        user.set_password(serializer.validated_data['password'])
        user.save()
        try:
            Driver.objects.create(user=user, phone_number=serializer.validated_data['phone_number'],
                                  birth_date=serializer.validated_data['birth_date'], added_by=self.request.user,
                                  location=serializer.validated_data['location'])
            return Response(serializer.data, status.HTTP_201_CREATED)
        except:
            user.delete()
            return Response({'error': 'Something went wrong. Try again.'}, status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        drivers = self.queryset
        data = []
        for driver in drivers:
            obj = {}
            obj['driver'] = DriverSerializer(driver, many=False).data
            trips = Trips.objects.filter(driver=driver.user)
            count = 0
            for trip in trips:
                duty_list = trip.duty_hour.split(':')
                total_duty_in_seconds = (int(duty_list[0]) * 3600) + (int(duty_list[1]) * 60)
                count += total_duty_in_seconds
            obj['duty_hours'] = round(count / 3600)
            obj['holidays'] = Leave.objects.filter(driver=driver.user).filter(leave_status='Approved').count()
            obj['leave_requests'] = Leave.objects.filter(driver=driver.user, leave_status='Pending').count()
            data.append(obj)
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        context = {'driver': DriverSerializer(instance, many=False).data}
        trips = Trips.objects.filter(driver=instance.user).order_by('-start_date')
        extra_data = []
        temp = []
        for trip in trips:
            m = str(trip.start_date.year) + '-' + str(trip.start_date.strftime("%B"))
            duty_list = trip.duty_hour.split(':')
            total_duty_in_seconds = (int(duty_list[0]) * 3600) + (int(duty_list[1]) * 60)
            if m in temp:
                index = temp.index(m)
                extra_data[index]['duty_hours'] += total_duty_in_seconds
            else:
                extra_data.append({'date': m, 'duty_hours': total_duty_in_seconds, 'holidays': 0})
                temp.append(m)

        for ex in extra_data:
            ex['duty_hours'] = round(ex['duty_hours'] / 3600)

        leaves = Leave.objects.filter(driver=instance.user).order_by('-from_date')
        for leave in leaves:
            m = str(leave.from_date.year) + '-' + str(leave.from_date.strftime("%B"))
            diff = (leave.to_date - leave.from_date).days
            if m in temp:
                index = temp.index(m)
                extra_data[index]['holidays'] += diff
            else:
                extra_data.append({'date': m, 'duty_hours': 0, 'holidays': diff})
                temp.append(m)
        context['activity'] = extra_data
        return Response(context)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            driver = User.objects.get(id=instance.user.id)
            driver.delete()
            return Response({'success': 'Driver is deleted.'}, status.HTTP_204_NO_CONTENT)
        except:
            return Response({'error': 'Driver with this ID is not found.'}, status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DriverUpdateSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(id=instance.user.id)
        user.first_name = serializer.validated_data['first_name']
        if user.email != serializer.validated_data['email']:
            if User.objects.filter(email=serializer.validated_data['email']).exists():
                return Response({'email': 'Email already exists'}, status.HTTP_400_BAD_REQUEST)
            user.email = serializer.validated_data['email']
        user.last_name = serializer.validated_data['last_name']
        if instance.phone_number != serializer.validated_data['phone_number']:
            if Driver.objects.filter(phone_number=serializer.validated_data['phone_number']).exists():
                return Response({'phone_number': 'Phone number already exists'}, status.HTTP_400_BAD_REQUEST)
            instance.phone_number = serializer.validated_data['phone_number']
        user.save()
        instance.birth_date = serializer.validated_data['birth_date']
        instance.location = serializer.validated_data['location']
        instance.save()
        return Response(request.data)


class EmployeeAPIView(GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin):
    queryset = Employee.objects.all()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UpdateEmployeeSerializer
        else:
            return EmployeeSerializer

    def create(self, request, *args, **kwargs):
        serializer = EmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.create(
            username=serializer.validated_data['user']['username'],
            email=serializer.validated_data['user']['email'],
            first_name=serializer.validated_data['user']['first_name'],
            last_name=serializer.validated_data['user']['last_name']
        )
        user.set_password(serializer.validated_data['user']['password'])
        user.is_staff = True
        user.save()
        try:
            Employee.objects.create(user=user, phone_number=serializer.validated_data['phone_number'],
                                    can_add_driver=serializer.validated_data['can_add_driver'],
                                    can_accept_leave_requests=serializer.validated_data['can_accept_leave_requests'], location=serializer.validated_data['location'])
            return Response(serializer.data)
        except:
            user.delete()
            return Response({'error': 'Something went wrong. Try again.'}, status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        s = self.get_object()
        user = User.objects.get(id=s.user.id)
        user.delete()
        return Response({}, status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = UpdateEmployeeSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            ph = Employee.objects.get(phone_number=serializer.validated_data['phone_number'])
            if instance != ph:
                return Response({'error': 'Phone number must be unique. This number is used by other employee'},
                                status.HTTP_400_BAD_REQUEST)
        except:
            pass
        try:
            em = Employee.objects.get(user__email=serializer.validated_data['user']['email'])
            if em != instance:
                return Response({'error': 'Email must be unique. This email is used by other employee'},
                                status.HTTP_400_BAD_REQUEST)
        except:
            pass

        user = User.objects.get(id=instance.user.id)
        user.first_name = serializer.validated_data['user']['first_name']
        user.last_name = serializer.validated_data['user']['last_name']
        user.email = serializer.validated_data['user']['email']
        user.save()
        instance.phone_number = serializer.validated_data['phone_number']
        instance.can_add_driver = serializer.validated_data['can_add_driver']
        instance.can_accept_leave_requests = serializer.validated_data['can_accept_leave_requests']
        instance.location = serializer.validated_data['location']
        instance.save()
        return Response(serializer.data)


class DriverListForLeaveAPIView(GenericViewSet, mixins.ListModelMixin):
    serializer_class = DriverForLeaveSerializer
    queryset = Driver.objects.all()


class LeaveRequestAPIView(GenericViewSet,
                          mixins.ListModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.CreateModelMixin):
    queryset = Leave.objects.all()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UpdateLeaveSerializer
        elif self.action == 'create':
            return CreateLeaveSerializer
        else:
            return LeaveRequestSerializer

    def update(self, request, *args, **kwargs):
        staff = Employee.objects.get(user=self.request.user)
        if staff.can_accept_leave_requests is False:
            return Response({'detail': 'You are not authorized to update leave'}, status.HTTP_401_UNAUTHORIZED)
        instance = self.get_object()
        serializer = UpdateLeaveSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(status_updated_by=self.request.user)
        return Response(serializer.data)


class LoggedInStaffUserInfoAPIView(GenericViewSet, mixins.ListModelMixin, ):
    serializer_class = LoggedInEmployeeSerializer
    queryset = Employee.objects.all()

    def list(self, request, *args, **kwargs):
        if self.request.user.is_staff:
            try:
                return Response(self.serializer_class(Employee.objects.get(user=self.request.user), many=False).data)
            except:
                return Response({'detail': 'No permission data found'}, status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'User is not a staff'}, status.HTTP_401_UNAUTHORIZED)


class ProfileAPIView(GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    serializer_class = EmployeeProfileSerializer
    queryset = Employee.objects.all()

    def list(self, request, *args, **kwargs):
        try:
            employee = Employee.objects.get(user=self.request.user)
            return Response(self.serializer_class(employee, many=False).data)
        except:
            return Response({'error': 'Profile info doesn\'t found'}, status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = Employee.objects.get(user=self.request.user)
        try:
            ph = Employee.objects.get(phone_number=serializer.validated_data['phone_number'])
            if employee != ph:
                return Response({'error': 'Phone number must be unique. This number is used by other employee'},
                                status.HTTP_400_BAD_REQUEST)
        except:
            pass
        try:
            em = Employee.objects.get(user__email=serializer.validated_data['user']['email'])
            if em != employee:
                return Response({'error': 'Email must be unique. This email is used by other employee'},
                                status.HTTP_400_BAD_REQUEST)
        except:
            pass

        user = User.objects.get(id=self.request.user.id)
        user.first_name = serializer.validated_data['user']['first_name']
        user.last_name = serializer.validated_data['user']['last_name']
        user.email = serializer.validated_data['user']['email']
        user.save()
        employee.phone_number = serializer.validated_data['phone_number']
        employee.save()
        return Response(serializer.data, status.HTTP_200_OK)


class CalendarFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [coreapi.Field(
            name='month',
            location='query',
            required=True,
            type='integer',
            description='Month in numeric format. e.g January will be 1, February will be 2, December will be 12',
            example='12'
        ), coreapi.Field(
            name='year',
            location='query',
            required=True,
            type='number'
        )]


class CalendarAPIView(GenericViewSet, mixins.ListModelMixin):
    serializer_class = CalendarSerializer
    queryset = Leave.objects.all()
    filter_backends = [CalendarFilterBackend]

    def list(self, request, *args, **kwargs):
        month = 0
        year = 0
        if request.GET.get('month'):
            try:
                if int(request.GET.get('month')) > 12 or int(request.GET.get('month')) < 1:
                    return Response({'error': 'Invalid month number'})
                else:
                    month = int(request.GET.get('month'))
            except:
                return Response({'error': 'Invalid month number'})

        if request.GET.get('year'):
            try:
                year = int(request.GET.get('year'))
            except:
                return Response({'error': 'Invalid year number'})
        from_date = None
        to_date = None
        if month > 0 and year > 0:
            month_range = calendar.monthrange(year, month)
            from_date = datetime(year, month, month_range[0], 0, 0, 0)
            to_date = datetime(year, month, month_range[1], 23, 59, 59)
        leaves = Leave.objects.all()
        if from_date and to_date:
            leaves = leaves.filter(from_date__gte=from_date, to_date__lte=to_date)
        spanData = [
            {"title": "approved vacation", 'code': 'u', 'value': leaves.filter(leave_type='Krank').count()},
            {"title": "planned vacation", "code": "gu", 'value': leaves.filter(leave_type='Urlaub').count()},
            {"title": "special leave", "code": "su", 'value': leaves.filter(leave_type='Sonderurlaub').count()},
            {"title": "time compensation", "code": "zu",
             'value': leaves.filter(leave_type='Zeitausgleich').count()},
            {'title': 'Total', 'code': '', 'value': leaves.count()}
        ]
        drivers = Driver.objects.all()
        leaveList = []
        for driver in drivers:
            d = {'name': driver.user.get_full_name()}
            leave = leaves.filter(driver=driver.user)
            for l in leave:
                d[
                    l.from_date.day] = 'u' if l.leave_type == 'Krank' else 'gu' if l.leave_type == 'Urlaub' else 'su' if l.leave_type == 'Sonderurlaub' else 'zu'
            leaveList.append(d)
        context = {
            'spanData': spanData,
            'employeeLeaves': leaveList
        }

        return Response(context)


class HolidayAPIView(ModelViewSet):
    serializer_class = HolidaySerializer
    queryset = Holidays.objects.all()

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsSuperUser]
        else:
            self.permission_classes = [IsAuthenticated]
        return super(ModelViewSet, self).get_permissions()
