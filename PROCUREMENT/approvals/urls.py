"""Approval URL configuration.

The router handles the approval viewsets, and the extra API-root entries make
the function-based approval workflows visible from the DRF landing page too.
"""

from django.urls import include, path

from PROCUREMENT.api_router import ExtendedDefaultRouter
from collections import OrderedDict
from . import views


router = ExtendedDefaultRouter()

# Purchase Requisition Approval Level 1
router.register(
    r"pr-approval-level1",
    views.PRApprovalLevel1ViewSet,
    basename="pr-approval-level1",
)

# Purchase Requisition Approval Level 2
router.register(
    r"pr-approval-level2",
    views.PRApprovalLevel2ViewSet,
    basename="pr-approval-level2",
)

# GRN Approval Level 1
router.register(
    r"grn-approval-level1",
    views.GRNApprovalLevel1ViewSet,
    basename="grn-approval-level1",
)

# GRN Approval Level 2
router.register(
    r"grn-approval-level2",
    views.GRNApprovalLevel2ViewSet,
    basename="grn-approval-level2",
)

# SRN Approval Level 1
router.register(
    r"srn-approval-level1",
    views.SRNApprovalLevel1ViewSet,
    basename="srn-approval-level1",
)

# SRN Approval Level 2
router.register(
    r"srn-approval-level2",
    views.SRNApprovalLevel2ViewSet,
    basename="srn-approval-level2",
)

router.extra_api_root_dict =  OrderedDict ({
    "sales-order-approval": "sales-order-approval-list",
    "po-approval-level1": "po-approval-level-1-list",
    "po-approval-level2": "po-approval-level-2-list",
    "po-approval-level3": "po-approval-level-3-list",
})

# Sales order approval endpoints
sales_order_approval_patterns = [
    path(
        "sales-order-approval/",
        views.sales_order_approval_list,
        name="sales-order-approval-list",
    ),
    path(
        "sales-order-approval/<int:pk>/",
        views.sales_order_approval_detail,
        name="sales-order-approval-detail",
    ),
]

po_approval_patterns = [
    path(
        "po-approval/level-1/",
        views.po_approval_level_1_list,
        name="po-approval-level-1-list",
    ),
    path(
        "po-approval/level-2/",
        views.po_approval_level_2_list,
        name="po-approval-level-2-list",
    ),
    path(
        "po-approval/level-3/",
        views.po_approval_level_3_list,
        name="po-approval-level-3-list",
    ),
    path(
        "po-approval/<int:pk>/action/",
        views.po_approval_action,
        name="po-approval-action",
    ),
]

urlpatterns = [
    path("", include(router.urls)),
] + sales_order_approval_patterns + po_approval_patterns
