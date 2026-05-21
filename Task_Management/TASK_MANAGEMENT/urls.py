from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [

    # ADMIN
    path(
        "admin/",
        admin.site.urls
    ),

    # TOKEN AUTH
    path(
        "api-token-auth/",
        obtain_auth_token,
        name="api_token_auth"
    ),

    # TASKS API
    path(
        "api/",
        include("tasks.urls")
    ),

    # FOLLOWUPS API
    path(
        "api/",
        include("followups.urls")
    ),

    # SWAGGER SCHEMA
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema"
    ),

    # SWAGGER DOCS
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema"
        ),
        name="swagger-ui"
    ),
]