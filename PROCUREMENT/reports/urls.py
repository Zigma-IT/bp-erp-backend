"""Report URL configuration with a browsable DRF index."""

from django.urls import include, path
from collections import OrderedDict
from PROCUREMENT.api_router import ExtendedDefaultRouter

from . import views


router = ExtendedDefaultRouter()
router.extra_api_root_dict = OrderedDict ({
    "pending-pr-report": "pending-pr-report",
    "complete-pr-report": "complete-pr-report",
    "po-report": "po-report",
    "pending-grn-report": "pending-grn-report",
    "complete-grn-report": "complete-grn-report",
    "pending-srn-report": "pending-srn-report",
    "complete-srn-report": "complete-srn-report",
})

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

# Pending GRN
pending_grn_patterns = [
    path('pending-grn-report/', views.PendingGRNReportView.as_view(), name='pending-grn-report'),
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


# Combine all patterns.
urlpatterns = [path("", include(router.urls))] + [
    *pending_pr_patterns,
    *complete_pr_patterns,
    *po_report_patterns,
    *pending_grn_patterns,
    *complete_grn_patterns,
    *pending_srn_patterns,
    *complete_srn_patterns,
]
