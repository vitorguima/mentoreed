from django.conf import settings
from django.contrib import admin
from drf_yasg import openapi
from django.urls import path
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Authors Haven API",
        default_version="v1",
        description="API endpoints for Authors Haven API Course",
        contact=openapi.Contact(email="api.imperfect@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0)),
    path(settings.ADMIN_URL, admin.site.urls),
]
