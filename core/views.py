from datetime import datetime
import datetime as dt
import math
import xlwt
from django.contrib.auth.models import User
from django.http import HttpResponse
from rest_framework import mixins, viewsets, status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from django.shortcuts import redirect, render

from account.models import Driver
from core.models import Leave, Activities, SleepMode, Trips, Holidays
from core.serializers import LeaveSerializer, ActivitySerializer, CurrentUserActivitySerializer, \
    SleepStartSerializer, SleepEndSerializer, TripSerializer, TripCreateSerializer, ActivityStopSerializer
from django.views import View


def home(request):
    return redirect('schema-swagger-ui')


class LeaveAPIView(viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin):
    serializer_class = LeaveSerializer
    queryset = Leave.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(driver=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        try:
            leave = Leave.objects.get(id=self.kwargs['pk'])
            if leave.driver == self.request.user:
                serializer = self.serializer_class(leave, many=False)
                return Response(serializer.data, status.HTTP_200_OK)
            else:
                return Response({'error': 'Unauthorized access'}, status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error': 'No leave found with this ID'}, status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance.driver == self.request.user:
            if instance.leave_status != 'Pending':
                return Response({'error': 'Only pending leave can be updated'}, status.HTTP_406_NOT_ACCEPTABLE)
            self.perform_update(serializer)
            return Response(serializer.data)
        else:
            return Response({'error': 'You are not authorized to update'}, status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        data = Leave.objects.filter(driver=self.request.user)
        return Response(self.serializer_class(data, many=True).data, status.HTTP_200_OK)


class ActivityStart(CreateAPIView):
    serializer_class = ActivitySerializer
    queryset = Activities.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            duty = Activities.objects.get(driver=self.request.user)
            return Response({'error': 'Already a duty is running'}, status.HTTP_400_BAD_REQUEST)
        except:
            serializer.save(driver=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class CurrentUserActivity(ListAPIView):
    serializer_class = CurrentUserActivitySerializer
    queryset = Activities.objects.all()

    def list(self, request, *args, **kwargs):
        try:
            activity = Activities.objects.get(driver=self.request.user)
            sleep = SleepMode.objects.filter(activity=activity).order_by("sleep_start_date")
            activity.sleep = sleep
            serializer = self.serializer_class(activity, many=False)
            return Response(serializer.data, status.HTTP_200_OK)
        except:
            return Response({'error': 'No duty found'}, status.HTTP_404_NOT_FOUND)


class ActivitySleepStart(CreateAPIView):
    serializer_class = SleepStartSerializer
    queryset = SleepMode.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            pass
        else:
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        try:
            activity = Activities.objects.get(driver=self.request.user)
            if activity.status == 'Sleeping':
                return Response({'error': 'Your duty already in sleep mode'}, status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error': 'No duty found'}, status.HTTP_404_NOT_FOUND)
        serializer.save(activity=activity)
        activity.activity_type = 'Sleep'
        activity.status = 'Sleeping'
        activity.save()
        return Response(serializer.data, status.HTTP_200_OK)


class ActivityResume(CreateAPIView):
    serializer_class = SleepEndSerializer
    queryset = SleepMode.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            pass
        else:
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        try:
            activity = Activities.objects.get(driver=self.request.user)
            if activity.status == 'Running':
                return Response({'error': 'Your duty already in running mode'}, status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error': 'No duty found'}, status.HTTP_404_NOT_FOUND)
        activity.activity_type = 'Duty'
        activity.status = 'Running'
        activity.save()
        instance = SleepMode.objects.filter(activity=activity).last()
        instance.sleep_end = serializer.data['sleep_end']
        instance.sleep_end_date = serializer.data['sleep_end_date']
        instance.save()
        return Response(self.serializer_class(instance, many=False).data, status.HTTP_201_CREATED)


class ActivityStop(CreateAPIView):
    serializer_class = ActivityStopSerializer
    queryset = Activities.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            pass
        else:
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        try:
            activity = Activities.objects.get(driver=self.request.user)
            activity.status = 'Stopped'
            activity.end_date = serializer.data['end_date']
            activity.end_time = serializer.data['end_time']
            activity.save()
            sleeps = SleepMode.objects.filter(activity=activity).last()
            if sleeps:
                sleeps.sleep_end = serializer.data['end_time']
                sleeps.sleep_end_date = serializer.data['end_date']
                sleeps.save()
            return Response(self.serializer_class({'status': 'Trip is completed!'}, many=False).data,
                            status.HTTP_201_CREATED)
        except:
            return Response(self.serializer_class({'status': 'No duty found!'}, many=False).data,
                            status.HTTP_404_NOT_FOUND)


class AuthenticatedUserTrip(ListAPIView):
    serializer_class = TripSerializer
    queryset = Trips.objects.all()

    def list(self, request, *args, **kwargs):
        activity = Activities.objects.get(driver=self.request.user)
        obj = {
            "driver": self.request.user.id,
            "trip_start_date": activity.start_date,
            "trip_start_time": activity.start_time
        }
        sleep = SleepMode.objects.filter(activity=activity)
        obj['sleep_data'] = sleep
        sleep_duration = 0
        if sleep.exists():
            for sl in sleep:
                sleep_start = datetime.combine(sl.sleep_start_date, sl.sleep_start)
                sleep_end = datetime.combine(sl.sleep_end_date, sl.sleep_end)
                sStartdate = datetime(sleep_start.year, sleep_start.month, sleep_start.day, sleep_start.hour,
                                      sleep_start.minute, sleep_start.second)
                sEnddate = datetime(sleep_end.year, sleep_end.month, sleep_end.day, sleep_end.hour,
                                    sleep_end.minute,
                                    sleep_end.second)
                duration = sEnddate - sStartdate
                sleep_duration += duration.seconds
            obj['total_sleep_hour'] = self.get_time_in_hour_minute(sleep_duration)
        else:
            obj['total_sleep_hour'] = '00:00'

        obj['trip_end_date'] = activity.end_date
        obj['trip_end_time'] = activity.end_time

        duty_start = datetime.combine(activity.start_date, activity.start_time)
        duty_end = datetime.combine(activity.end_date, activity.end_time)
        duty_duration = duty_end - duty_start
        total_duty = duty_duration.total_seconds() - sleep_duration
        obj['total_duty_hour'] = self.get_time_in_hour_minute(total_duty)
        return Response(self.serializer_class(obj, many=False).data, status.HTTP_200_OK)

    def get_time_in_hour_minute(self, seconds):
        if math.floor(seconds / 3600) < 10:
            sleep_hour = '0' + str(math.floor(seconds / 3600))
        else:
            sleep_hour = str(math.floor(seconds / 3600))
        if math.floor((seconds % 3600) / 60) < 10:
            sleep_minute = '0' + str(math.floor((seconds % 3600) / 60))
        else:
            sleep_minute = str(math.floor((seconds % 3600) / 60))
        return sleep_hour + ':' + sleep_minute


class AuthenticateDriverTripCreateAPIView(CreateAPIView,
                                          ListAPIView):
    serializer_class = TripCreateSerializer
    queryset = Trips.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(driver=self.request.user)
        activity = Activities.objects.get(driver=self.request.user)
        activity.delete()
        return Response(serializer.data, status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(driver=self.request.user)
        return Response(self.serializer_class(queryset, many=True).data, status.HTTP_200_OK)


"""
All views for report will be here.
"""


class DriversView(View):
    def get(self, request):
        driver = Driver.objects.all()
        return render(request, 'drivers.html', {'drivers': driver})


class DownloadExpense(View):
    holidayList = [datetime(2021, 1, 3), datetime(2021, 4, 2), datetime(2021, 4, 5), datetime(2021, 5, 1),
                   datetime(2021, 5, 13), datetime(2021, 5, 24), datetime(2021, 6, 3), datetime(2021, 10, 3),
                   datetime(2021, 11, 1), datetime(2021, 12, 25),
                   datetime(2021, 12, 26)]

    def get(self, request, username):

        user = User.objects.get(username=username)
        trips = Trips.objects.filter(driver__username=username)
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="Spesen.xls"'

        wb = xlwt.Workbook(encoding='utf-8')
        meal_allowence_sheet = wb.add_sheet('Verpflegungspauschalen')
        allowence_list = [['Stunden', 'Pauschale'], [0, 0], [8, 14], [23.98, 28]]
        for i in range(len(allowence_list)):
            for j in range(len(allowence_list[i])):
                meal_allowence_sheet.write(i, j, allowence_list[i][j])

        d = datetime.today()
        holiday_sheet = wb.add_sheet('Feiertage ' + str(d.year))
        holidays = Holidays.objects.all()
        holiday_sheet.write(0, 0, 'Feiertage ' + str(d.year))
        hIndex = 1
        holiday_date_format = xlwt.XFStyle()
        holiday_date_format.num_format_str = 'dd-mm-yyyy'
        for holiday in holidays:
            holiday_sheet.write(hIndex, 0, holiday.date, holiday_date_format)
            holiday_sheet.write(hIndex, 1, holiday.title)
            holiday_sheet.write(hIndex, 2, 'FT')
            hIndex += 1

        calendar_sheet = wb.add_sheet('Kalender')
        d1 = dt.date(d.year, 1, 1)
        d2 = dt.date(d.year, 12, 31)
        days = [d1 + dt.timedelta(days=x) for x in range((d2 - d1).days + 1)]
        calendar_sheet.write(0, 0, 'Datum')
        calendar_sheet.write(0, 1, 'Wochentag')
        calendar_sheet.write(0, 2, 'Wochentag')
        cIndex = 1
        for day in days:
            calendar_sheet.write(cIndex, 0, day, holiday_date_format)
            calendar_sheet.write(cIndex, 1, xlwt.Formula('WEEKDAY(A' + str(cIndex + 1) + ',2)'))
            calendar_sheet.write(cIndex, 2, xlwt.Formula(
                'IF(E' + str(cIndex + 1) + '="FT","FT",IF(B' + str(cIndex + 1) + '=1,"MO",IF(B' + str(
                    cIndex + 1) + '=2,"DI",IF(B' + str(cIndex + 1) + '=3,"MI",IF(B' + str(
                    cIndex + 1) + '=4,"DO",IF(B' + str(cIndex + 1) + '=5,"FR",IF(B' + str(
                    cIndex + 1) + '=6,"SA",IF(B' + str(cIndex + 1) + '=7,"SO","Werktag"))))))))'))
            cIndex += 1
        expense_sheet = wb.add_sheet(username)
        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        # Expense title in second row
        expense_sheet.write(1, 0, 'Spesenzettel', font_style)
        expense_sheet.write(1, 2, 'Feb-2021', font_style)
        # Driver name in 4rth row
        expense_sheet.write(3, 0, 'Arbeitnehmer:', font_style)
        expense_sheet.write(3, 1, user.get_full_name())
        columns = ['Datum', 'Wochentag', 'Abfahrt Betriebsstätte', 'Ankunft Betriebsstätte', 'Formeln', 'Formeln',
                   'Stunden', 'Verpfl. Mehraufwand', 'Beginn Nachtpause', 'Ende Nachtpause', 'Formeln', 'Formeln',
                   'Stunden SO', 'Stunden FT', 'Formel', 'NZ 40% 0-4Uhr', 'Formel',
                   'NZ 25% 20 - 24 Uhr 4 - 6 Uhr abzgl. NZ 40%', 'Sonntag',
                   'Feiertag', 'Bemerkung', 'Einsatzab-hängige Vergütung Samstag',
                   'Einsatzab-hängige Vergütung Sonntags']
        for col_num in range(len(columns)):
            expense_sheet.write(5, col_num, columns[col_num], font_style)

        row_num = 6
        data = []
        for trip in trips:
            x = [trip.start_date, trip.start_date.weekday(), trip.duty_start_time, trip.duty_end_time]  # 4
            startTime = datetime.combine(trip.start_date, trip.duty_start_time)
            endTime = datetime.combine(trip.start_date, trip.duty_end_time)
            duty = endTime - startTime
            total_duty_hour = self.get_time_in_hour_minute(duty.total_seconds())
            x.append(total_duty_hour)  # 5

            date_time = datetime.strptime(total_duty_hour + ':00', "%H:%M:%S")
            a_timedelta = date_time - datetime(1900, 1, 1)
            seconds = a_timedelta.total_seconds()
            if 28800 <= seconds < 86340:
                x.append('14')  # 6
            elif seconds >= 86340:
                x.append('28')  # 6
            else:
                x.append('0')  # 6
            x.append(trip.sleep_start_time)  # 7
            x.append(trip.sleep_end_time)  # 8
            data.append(x)

        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'
        time_format = xlwt.XFStyle()
        time_format.num_format_str = 'hh:mm AM/PM'

        diffTime = xlwt.XFStyle()
        diffTime.num_format_str = 'HH:MM'
        for instances in data:
            for col_num in range(len(instances)):
                if col_num == 0:
                    expense_sheet.write(row_num, col_num, instances[col_num], date_format)  # Start date
                elif col_num == 1:
                    expense_sheet.write(row_num, col_num, xlwt.Formula(
                        'VLOOKUP(A' + str(row_num + 1) + ',Kalender!A1:C367,3,FALSE)'))  # Start Time
                elif col_num == 2 or col_num == 3:
                    if col_num == 2:
                        expense_sheet.write(row_num, 4, xlwt.Formula('C' + str(row_num + 1) + '*24'))
                    if col_num == 3:
                        expense_sheet.write(row_num, 5, xlwt.Formula('ROUNDUP(D' + str(row_num + 1) + '*24,2)'))
                    expense_sheet.write(row_num, col_num, instances[col_num], time_format)  # End time
                elif col_num == 4:
                    # expense_sheet.write(row_num, 6, instances[col_num])  # Duty hour = end time -  start time
                    expense_sheet.write(row_num, 6,
                                        xlwt.Formula('(ABS(F' + str(row_num + 1) + '-E' + str(row_num + 1) + '))'))
                elif col_num == 5:
                    # meal_price_total += int(instances[col_num])
                    expense_sheet.write(row_num, 7, xlwt.Formula('IF(D' + str(row_num + 1) + '="","",VLOOKUP(G' + str(
                        row_num + 1) + ',Verpflegungspauschalen!$A$2:$B$4,2,TRUE))'))
                    # expense_sheet.write(row_num, 7, int(instances[col_num]))  # Paid for meal
                elif col_num == 6:
                    expense_sheet.write(row_num, 8, instances[col_num], time_format)  # Sleep time start
                    expense_sheet.write(row_num, 10, xlwt.Formula('ROUNDUP(I' + str(row_num + 1) + '*24,2)'))
                elif col_num == 7:
                    expense_sheet.write(row_num, 9, instances[col_num], time_format)  # Sleep time end
                    expense_sheet.write(row_num, 11, xlwt.Formula('ROUNDUP(J' + str(row_num + 1) + '*24,2)'))
                    expense_sheet.write(row_num, 12, xlwt.Formula(
                        'IF(I' + str(row_num + 1) + '="","",IF(AND(B' + str(row_num + 1) + '="SO",L' + str(
                            row_num + 1) + '>K' + str(row_num + 1) + '),MOD(L' + str(row_num + 1) + '-K' + str(
                            row_num + 1) + ',24),IF(AND(B' + str(row_num + 1) + '="SO",K' + str(
                            row_num + 1) + '<24),(24-K' + str(row_num + 1) + ')+(IF(L' + str(
                            row_num + 1) + '>4,4,L' + str(
                            row_num + 1) + ')),0)))'))
                    expense_sheet.write(row_num, 13, xlwt.Formula(
                        'IF(I' + str(row_num + 1) + '="","",IF(AND(B' + str(row_num + 1) + '="FT",L' + str(
                            row_num + 1) + '>K' + str(row_num + 1) + '),MOD(L' + str(row_num + 1) + '-K' + str(
                            row_num + 1) + ',24),IF(AND(B' + str(row_num + 1) + '="FT",K' + str(
                            row_num + 1) + '<24),(24-K' + str(row_num + 1) + ')+(IF(L' + str(
                            row_num + 1) + '>4,4,L' + str(row_num + 1) + ')),0)))'))
                    expense_sheet.write(row_num, 14, xlwt.Formula(
                        'IF(B' + str(row_num + 1) + '="FT",0,IF(I' + str(row_num + 1) + '>J' + str(
                            row_num + 1) + ',MIN(J' + str(row_num + 1) + ',4/24),0))'))
                    expense_sheet.write(row_num, 15, xlwt.Formula(
                        'IF(O' + str(row_num + 1) + '*24=0,"",O' + str(row_num + 1) + '*24)'))
                    # expense_sheet.write(row_num, 16, xlwt.Formula(
                    #     'IF(B' + str(row_num + 1) + '="SO",IF(AND(J' + str(row_num + 1) + '>I' + str(
                    #         row_num + 1) + ',I' + str(row_num + 1) + '<6/24),MIN(J' + str(
                    #         row_num + 1) + ',6/24)-I' + str(row_num + 1) + ',IF(AND(J' + str(row_num + 1) + '>I' + str(
                    #         row_num + 1) + ',J' + str(row_num + 1) + '>20/24),J' + str(row_num + 1) + '-MAX(I' + str(
                    #         row_num + 1) + ',20/24),IF(I' + str(row_num + 1) + '>J' + str(
                    #         row_num + 1) + ',1-MAX(I' + str(row_num + 1) + ',20/24)+IF(J' + str(
                    #         row_num + 1) + '>4/24,MIN(J' + str(row_num + 1) + ',6/24)-4/24,0),0))),IF(B' + str(
                    #         row_num + 1) + '="FT",0,IF(B' + str(row_num + 1) + '<>"FT",IF(AND(J' + str(
                    #         row_num + 1) + '>I' + str(row_num + 1) + ',I' + str(row_num + 1) + '<6/24),MIN(J' + str(
                    #         row_num + 1) + ',6/24)-I' + str(row_num + 1) + ',IF(AND(J' + str(row_num + 1) + '>I' + str(
                    #         row_num + 1) + ',J' + str(row_num + 1) + '>20/24),J' + str(row_num + 1) + '-MAX(I' + str(
                    #         row_num + 1) + ',20/24),IF(I' + str(row_num + 1) + '>J' + str(
                    #         row_num + 1) + ',1-MAX(I' + str(row_num + 1) + ',20/24)+IF(J' + str(
                    #         row_num + 1) + '>4/24,MIN(J' + str(row_num + 1) + ',6/24)-4/24,0),0))))))'))
                    expense_sheet.write(row_num, 17, xlwt.Formula('Q' + str(row_num + 1) + '*24'))
                    expense_sheet.write(row_num, 18, xlwt.Formula(
                        'IF(B' + str(row_num + 1) + '="Werktag",0,IF(B' + str(row_num + 1) + '="SA",0,IF(B' + str(
                            row_num + 1) + '="FT",0,IF(B' + str(row_num + 1) + '="SO",M' + str(row_num + 1) + ',0))))'))
                    expense_sheet.write(row_num, 19, xlwt.Formula(
                        'IF(B' + str(row_num + 1) + '="Werktag",0,IF(B' + str(row_num + 1) + '="SA",0,IF(B' + str(
                            row_num + 1) + '="FT",N' + str(row_num + 1) + ',IF(B' + str(row_num + 1) + '="SO",0,0))))'))
                    expense_sheet.write(row_num, 21, xlwt.Formula(
                        'IF(B' + str(row_num + 1) + '<>"SA","",IF(E' + str(row_num + 1) + '>0,(IF(L' + str(
                            row_num + 1) + '>K' + str(row_num + 1) + ',L' + str(row_num + 1) + '-K' + str(
                            row_num + 1) + ',(24-K' + str(row_num + 1) + '+L' + str(row_num + 1) + '))),0))'))
                    expense_sheet.write(row_num, 22, xlwt.Formula(
                        'IF(AND(OR(B' + str(row_num + 1) + '="SO",B' + str(row_num + 1) + '="FT"),I' + str(
                            row_num + 1) + '<>""),IF(L' + str(row_num + 1) + '>K' + str(row_num + 1) + ',L' + str(
                            row_num + 1) + '-K' + str(row_num + 1) + ',L' + str(row_num + 1) + '+24-K' + str(
                            row_num + 1) + '),"")'))
            row_num += 1

        expense_sheet.write(37, 3, 'Summe:')
        expense_sheet.write(37, 7, xlwt.Formula('SUM(H7:H' + str(36) + ')'))
        wb.save(response)
        return response

    def get_time_in_hour_minute(self, seconds):
        if math.floor(seconds / 3600) < 10:
            sleep_hour = '0' + str(math.floor(seconds / 3600))
        else:
            sleep_hour = str(math.floor(seconds / 3600))
        if math.floor((seconds % 3600) / 60) < 10:
            sleep_minute = '0' + str(math.floor((seconds % 3600) / 60))
        else:
            sleep_minute = str(math.floor((seconds % 3600) / 60))
        return sleep_hour + ':' + sleep_minute


def error_404_view(request, exception):
    return render(request, '404.html')
