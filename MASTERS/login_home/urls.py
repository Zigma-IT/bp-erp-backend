from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuthViewSet, DepartmentViewSet, EmployeeViewSet, ManualAttendanceViewSet


router = DefaultRouter()
router.register(r"auth", AuthViewSet, basename="auth")
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"employees", EmployeeViewSet, basename="employee")
router.register(r"attendance", ManualAttendanceViewSet, basename="attendance")


urlpatterns = [
    path("", include(router.urls)),
]
