from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    # Login page and Home page URls
    path('api/admin/', include('login_home.urls')),
    path('api/users/', include('admin_master.urls')),
    # Common Master Routes (Countries, States, Cities, Taxes)
    path('api/masters/', include('common_master.urls')),
    # Purchase Master Routes
    path('api/purchase/', include('purchase_master.urls')),
    # HR Master Routes
    path('api/masters/hr/', include('hr_master.urls')),
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),

]
