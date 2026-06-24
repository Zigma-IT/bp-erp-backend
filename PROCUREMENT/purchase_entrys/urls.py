"""Purchase entry URL configuration.

The extra API-root entries are kept descriptive so the DRF landing page reads
like a module index for whoever maintains the procurement APIs next.
"""

from django.urls import include, path
from collections import OrderedDict
from PROCUREMENT.api_router import ExtendedDefaultRouter

from . import views

router = ExtendedDefaultRouter()

# Rate order
router.register(r'rate-orders', views.RateOrderViewSet, basename='rate-order')

# GRN
router.register(r'grn', views.GRNViewSet, basename='grn')

# SRN
router.register(r'srn', views.SRNViewSet, basename='srn')

router.extra_api_root_dict = OrderedDict ({
    "dropdown-companies": "company-dropdown",
    "dropdown-projects": "project-dropdown",
    "dropdown-suppliers": "supplier-dropdown",
    "dropdown-products": "product-dropdown",
    "dropdown-units": "unit-dropdown",
    "dropdown-taxes": "tax-dropdown",
    "purchase-order-types": "purchase-order-types",
    "purchase-orders": "purchase-order-list",
    "purchase-orders-create": "purchase-order-create",
    "purchase-requisitions": "purchase-requisition-approval-list",
    "purchase-requisitions-create": "purchase-requisition-create",
    "purchase-order-approval-level1": "purchase-order-approval-level-1-list",
    "purchase-order-approval-level2": "purchase-order-approval-level-2-list",
    "purchase-order-approval-level3": "purchase-order-approval-level-3-list",
})


# Dropdown APIs used by the create/edit purchase-order screens.
dropdown_patterns = [
    path("dropdown/companies/", views.company_dropdown, name="company-dropdown"),
    path("dropdown/projects/", views.project_dropdown, name="project-dropdown"),
    path("dropdown/suppliers/", views.supplier_dropdown, name="supplier-dropdown"),
    path("dropdown/products/", views.product_dropdown, name="product-dropdown"),
    path("dropdown/items/", views.item_dropdown, name="item-dropdown"),
    path("dropdown/units/", views.unit_dropdown, name="unit-dropdown"),
    path("dropdown/taxes/", views.tax_dropdown, name="tax-dropdown"),
    path("dropdown/po-types/", views.purchase_order_types, name="purchase-order-types"),
]

# Main purchase-order APIs.
purchase_order_patterns = [
    path("purchase-orders/", views.purchase_order_list, name="purchase-order-list"),
    path(
        "purchase-orders/create/", views.create_purchase_order,name="purchase-order-create",),
    path(
        "purchase-orders/<int:pk>/",views.purchase_order_detail,name="purchase-order-detail",),
    path(
        "purchase-orders/<int:pk>/documents/",
        views.purchase_order_documents,
        name="purchase-order-documents",
    ),
    path(
        "purchase-orders/<int:pk>/documents/<int:document_id>/",
        views.delete_purchase_order_document,
        name="purchase-order-document-delete",
    ),
]

purchase_requisition_patterns = [
    path(
        "purchase-requisitions/sublist/",
        views.purchase_requisition_sublist,
        name="purchase-requisition-sublist",
    ),
    path(
        "purchase-requisitions/",views.purchase_requisition_approval_list,name="purchase-requisition-approval-list",),
    path(
        "purchase-requisitions/create/", views.create_purchase_requisition,name="purchase-requisition-create",),
    path(
        "purchase-requisitions/<int:pk>/",views.purchase_requisition_detail,name="purchase-requisition-detail",),
    path(
        "purchase-requisitions/<int:pk>/documents/",
        views.purchase_requisition_documents,
        name="purchase-requisition-documents",
    ),
    path(
        "purchase-requisitions/<int:pk>/documents/<int:document_id>/",
        views.delete_purchase_requisition_document,
        name="purchase-requisition-document-delete",
    ),
]

# Approval list and action APIs.
approval_patterns = [
    path(
        "purchase-orders/approval-level-1/",
        views.purchase_order_approval_level_1_list,
        name="purchase-order-approval-level-1-list",
    ),
    path(
        "purchase-orders/approval-level-2/",
        views.purchase_order_approval_level_2_list,
        name="purchase-order-approval-level-2-list",
    ),
    path(
        "purchase-orders/approval-level-3/",
        views.purchase_order_approval_level_3_list,
        name="purchase-order-approval-level-3-list",
    ),
    path(
        "purchase-orders/<int:pk>/approvals/<int:level>/",
        views.update_purchase_order_approval,
        name="purchase-order-approval-update",
    ),
]

# Legacy aliases are kept so the existing frontend can move to the cleaner
# namespaced URLs without a hard break.
legacy_patterns = [
    path("purchase_order/list/", views.purchase_order_list, name="legacy-po-list"),
    path(
        "purchase_order/create/",
        views.create_purchase_order,
        name="legacy-po-create",
    ),
    path(
        "purchase_order/<int:pk>/",
        views.purchase_order_detail,
        name="legacy-po-detail",
    ),
    path(
        "po/level_1/list/",
        views.purchase_order_approval_level_1_list,
        name="legacy-po-level-1-list",
    ),
    path(
        "po/level_2/list/",
        views.purchase_order_approval_level_2_list,
        name="legacy-po-level-2-list",
    ),
    path(
        "po/level_3/list/",
        views.purchase_order_approval_level_3_list,
        name="legacy-po-level-3-list",
    ),
]

# Combine all patterns
urlpatterns = [
    path("", include(router.urls)),
] + (
    dropdown_patterns
    + purchase_order_patterns
    + purchase_requisition_patterns
    + approval_patterns
    + legacy_patterns
)
