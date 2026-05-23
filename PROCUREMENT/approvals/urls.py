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
        "sales-order-approval/",views.sales_order_approval_list,name="sales-order-approval-list",),
    path(
        "sales-order-approval/<int:pk>/",views.sales_order_approval_detail,name="sales-order-approval-detail",),
]

# Sales invoice approval endpoints
sales_invoice_approval_patterns = [
    path(
        "sales-invoice-approval/",views.sales_invoice_approval_list,name="sales-invoice-approval-list",),
    path(
        "sales-invoice-approval/<int:pk>/",views.sales_invoice_approval_detail,name="sales-invoice-approval-detail",),
    path(
        "sales-invoice-approval/create/",views.sales_invoice_create,name="sales-invoice-create",),
    path(
        "sales-invoice-approval/<int:pk>/update/",views.sales_invoice_update,name="sales-invoice-update",),
]

urlpatterns = [
    path('', include(router.urls)),
] + sales_order_approval_patterns + sales_invoice_approval_patterns
