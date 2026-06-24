from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-token-auth/", obtain_auth_token, name="api_token_auth"),

    # ✅ Purchase procurement routes (ONLY ONE)
    path("api/purchase/", include("purchase_entrys.urls")),

    # Purchase expense routes
    path("api/purchase-expense/", include("purchase_expense.urls")),

    # Sales routes
    path("api/sales/", include("sales.urls")),

    # Approval routes
    path("api/approvals/", include("approvals.urls")),

    # Report routes
    path("api/reports/", include("reports.urls")),

    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]