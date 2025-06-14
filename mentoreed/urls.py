from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from core_apps.users.views import UserViewSet
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework import routers

from core_apps.jwt.urls import urlpatterns as jwt_urls

schema_view = get_schema_view(
    openapi.Info(
        title="Mentoreed API",
        default_version="v1",
        description="Mentoreed API documentation",
        contact=openapi.Contact(email="whatever@whatever.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()
router.register(r'api/v1/users', UserViewSet, basename='user')

urlpatterns = [
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0)),
    path(settings.ADMIN_URL, admin.site.urls),
    path('', include(router.urls)),
    path('api/v1/auth/', include('core_apps.jwt.urls')),
]

urlpatterns += jwt_urls
