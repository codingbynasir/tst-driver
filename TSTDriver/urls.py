"""TSTDriver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt import views as jwt_views
from core.views import home, DriversView, DownloadExpense

schema_view = get_schema_view(
    openapi.Info(
        title="TST drive API",
        default_version='v 1.2.0',
        description="TST driver API is a web api mainly for mobile application and dashboard web application. Here are 2 versions of API. v1 is for mobile application and v2 is for dashboard."
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('v1/api/', include('core.urls', namespace='core')),
    path('v1/api/user/', include('account.urls', namespace='account')),
    path('v1/auth/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('v1/auth/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('v1/auth/token/verify/', jwt_views.TokenVerifyView.as_view(), name='verify_token'),
    path('v2/api/', include('dashboard.urls')),
    path('doc/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('accounts/', include('rest_framework.urls', namespace='rest')),

    path('drivers/', DriversView.as_view(), name="all-driver"),
    path('drivers/expense/<username>/download/', DownloadExpense.as_view(), name="download-expense")
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.error_404_view'
admin.site.site_header = 'TST Driver'
admin.site.site_title = 'TST Driver'
admin.site.index_title = 'TST Driver'
