from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", include("core.urls")),
    path("api/v1/layers/", include("layers.urls")),
    path("api/v1/analysis/", include("analysis.urls")),
]
