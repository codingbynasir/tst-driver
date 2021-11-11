from django.contrib import admin
from core.models import Leave, Activities, SleepMode, Trips, Holidays


class LeaveModeAdmin(admin.ModelAdmin):
    class Meta:
        model = Leave

    list_display = ['__str__', 'leave_type', 'from_date', 'to_date', 'leave_status']
    list_filter = ['leave_type', 'from_date', 'to_date', 'leave_status']
    list_per_page = 20


admin.site.register(Leave, LeaveModeAdmin)


class ActivitiesAdmin(admin.ModelAdmin):
    class Meta:
        model = Activities

    list_display = ['__str__', 'activity_type', 'start_date', 'start_time', 'end_date', 'end_time', 'status']
    list_filter = ['activity_type', 'status']
    list_per_page = 20


admin.site.register(Activities, ActivitiesAdmin)
admin.site.register(SleepMode)


class TripAdmin(admin.ModelAdmin):
    class Meta:
        model = Trips

    list_display = ['__str__', 'start_date', 'end_date', 'sleep_hour', 'duty_hour']
    list_per_page = 20


admin.site.register(Trips, TripAdmin)


class HolidaysAdmin(admin.ModelAdmin):
    class Meta:
        model = Holidays

    list_display = ['date', 'title']
    list_per_page = 20


admin.site.register(Holidays, HolidaysAdmin)
