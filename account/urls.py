from rest_framework.routers import DefaultRouter

from account.views import RegisterAPIView, UpdateAPIView, OTPAPIView, OTPVerifyAPIView, ChangePassword, ProfileAPIView, \
    ProfileDetails

router = DefaultRouter()
router.register('register', RegisterAPIView, basename='register')
router.register('update', UpdateAPIView, basename='update')
router.register('otp', OTPAPIView, basename='otp')
router.register('otp/verify', OTPVerifyAPIView, basename='otp_verify')
router.register('change_password', ChangePassword, basename='change_password')
router.register('profile', ProfileAPIView, basename='profile')
router.register('detail', ProfileDetails, basename='profile_details')
app_name = 'account'
urlpatterns = router.urls
