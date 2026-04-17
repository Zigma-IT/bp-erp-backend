"""Sales URL configuration with a browsable DRF index."""

from django.urls import include, path
from collections import OrderedDict
from PROCUREMENT.api_router import ExtendedDefaultRouter

from . import views


router = ExtendedDefaultRouter()
router.extra_api_root_dict = OrderedDict ({
    "sales-orders": "sales-order-list",
    "sales-invoices": "sales-invoice-list",
    "ordered-bom": "ordered-bom-list",
    "expense-entry": "expense-entry-list",
    "expense-approval-action": "expense-approval-action",
})

# Sales order endpoints
sales_order_patterns = [
    path("sales-orders/", views.sales_order_list, name="sales-order-list"),
    path("sales-orders/<int:pk>/", views.sales_order_detail, name="sales-order-detail"),
]

sales_invoice_patterns = [
    path("sales-invoices/", views.sales_invoice_list, name="sales-invoice-list"),
    path("sales-invoices/<int:pk>/", views.sales_invoice_detail, name="sales-invoice-detail"),
]

Sales_BOM = [
    path("ordered-bom/", views.ordered_bom_list, name="ordered-bom-list"),
    path("ordered-bom/<int:pk>/", views.ordered_bom_detail, name="ordered-bom-detail"),

]

Purchase_Expense = [
    path("expense-entry/", views.expense_entry_list, name="expense-entry-list"),
    path("expense-entry/<int:pk>/", views.expense_entry_detail, name="expense-entry-detail"),
    path("expense-entry/approval-action/", views.expense_approval_action, name="expense-approval-action"),
]
# Combine all patterns.
urlpatterns = [path("", include(router.urls))] + (
    sales_order_patterns + sales_invoice_patterns + Sales_BOM + Purchase_Expense
)
