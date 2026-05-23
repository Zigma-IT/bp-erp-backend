from django.urls import path

from .views import TaskReportListAPIView


urlpatterns = [
    path(
        "task-reports/",
        TaskReportListAPIView.as_view(),
        name="task-report-list",
    ),
]
