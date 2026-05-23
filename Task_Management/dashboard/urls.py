# dashboard/urls.py

from django.urls import path

from .views import (
    DashboardKPIView,
    AgeAnalysisView,
    DepartmentWiseView,
    CompanyWiseView,
    ProjectWiseView,
    RemarkAnalysisView,
    MonthlyAnalyticsView,
    TaskListView
)

urlpatterns = [

    path(
        'kpi/',
        DashboardKPIView.as_view()
    ),

    path(
        'age-analysis/',    
        AgeAnalysisView.as_view()
    ),

    path(
        'department-wise/',
        DepartmentWiseView.as_view()
    ),

    path(
        'company-wise/',
        CompanyWiseView.as_view()
    ),

    path(
        'project-wise/',
        ProjectWiseView.as_view()
    ),

    path(
        'remark-analysis/',
        RemarkAnalysisView.as_view()
    ),

    path(
        'monthly-analytics/',
        MonthlyAnalyticsView.as_view()
    ),

    path(
        'tasks/',
        TaskListView.as_view()
    ),
]


