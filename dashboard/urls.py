from rest_framework.routers import DefaultRouter

from dashboard.views import DashboardAPIView, DriversAPIView, EmployeeAPIView, LeaveRequestAPIView, \
    LoggedInStaffUserInfoAPIView, ProfileAPIView, DriverListForLeaveAPIView, CalendarAPIView, HolidayAPIView

router = DefaultRouter()
router.register('dashboard', DashboardAPIView, basename='dashboard')
router.register('driver', DriversAPIView, basename='driver')
router.register('employee', EmployeeAPIView, basename='employee')
router.register('leave/drivers', DriverListForLeaveAPIView, basename='driver_for_leave')
router.register('leave', LeaveRequestAPIView, basename='leave')
router.register('permissions', LoggedInStaffUserInfoAPIView, basename='permissions')
router.register('profile', ProfileAPIView, basename='profile')
router.register('calendar', CalendarAPIView, basename='calendar')
router.register('holiday', HolidayAPIView, basename='holiday')
app_name = 'dashboard'
urlpatterns = router.urls
