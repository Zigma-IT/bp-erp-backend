from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-token-auth/", obtain_auth_token, name="api_token_auth"),
    # Primary procurement API namespace following the same project-level pattern
    # used in the MASTERS backend.
    path("api/purchase/", include("purchase_entrys.urls")),
    # Temporary alias for the older app-based URL prefix so existing frontend
    # calls do not break while the new structure is adopted.
    path("api/purchase_entrys/", include("purchase_entrys.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]
