from django.urls import path

from . import views

# Pending PR
pending_pr_patterns = [
    path('pending-pr-report/', views.PendingPRReportView.as_view(), name='pending-pr-report'),
]

# Complete PR
complete_pr_patterns = [
    path('complete-pr-report/', views.CompletePRReportView.as_view(), name='complete-pr-report'),
]

# PO Report
po_report_patterns = [
    path('po-report/', views.POReportView.as_view(), name='po-report'),
]

# Complete GRN
complete_grn_patterns = [
    path('complete-grn-report/', views.CompleteGRNReportView.as_view(), name='complete-grn-report'),
]

# Pending SRN
pending_srn_patterns = [
    path('pending-srn-report/', views.PendingSRNReportView.as_view(), name='pending-srn-report'),
]

# Complete SRN
complete_srn_patterns = [
    path('complete-srn-report/', views.CompleteSRNReportView.as_view(), name='complete-srn-report'),
]


# Combine all patterns
urlpatterns = (
    pending_pr_patterns
    + complete_pr_patterns
    + po_report_patterns
    + complete_grn_patterns
    + pending_srn_patterns
    + complete_srn_patterns
)
