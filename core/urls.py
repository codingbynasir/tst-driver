from django.urls import path
from rest_framework.routers import DefaultRouter

from core.views import LeaveAPIView, ActivityStart, CurrentUserActivity, ActivitySleepStart, ActivityResume, \
    AuthenticatedUserTrip, AuthenticateDriverTripCreateAPIView, ActivityStop

router = DefaultRouter()
router.register('leave', LeaveAPIView, basename='leave')
app_name = 'core'
urlpatterns = [
    path('activity/start/', ActivityStart.as_view(), name='activity_start'),
    path('activity/stop/', ActivityStop.as_view(), name='activity_stop'),
    path('activity/me/', CurrentUserActivity.as_view(), name='current_user_activity'),
    path('activity/sleep/start/', ActivitySleepStart.as_view(), name='activity_sleep'),
    path('activity/sleep/resume/', ActivityResume.as_view(), name='activity_resume'),
    path('trip/overview/', AuthenticatedUserTrip.as_view(), name='trip_overview'),
    path('trip/', AuthenticateDriverTripCreateAPIView.as_view(), name='trip'),
]+router.urls
