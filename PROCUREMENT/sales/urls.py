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
    path("ordered-bom/", views.ordered_bom_list, name="ordered-bom-list"),
    path("ordered-bom/<int:pk>/", views.ordered_bom_detail, name="ordered-bom-detail"),
    path("ordered-bom/<int:pk>/documents/", views.ordered_bom_documents, name="ordered-bom-documents"),
    path("ordered-bom/<int:pk>/documents/<int:document_id>/", views.ordered_bom_document_delete, name="ordered-bom-document-delete"),
]

# Sales invoice endpoints
sales_invoice_patterns = [
    path("sales-invoices/", views.sales_invoice_list, name="sales-invoice-list"),
    path("sales-invoices/<int:pk>/", views.sales_invoice_detail, name="sales-invoice-detail"),
    path("sales-invoices/<int:pk>/documents/", views.sales_invoice_documents, name="sales-invoice-documents"),
    path("sales-invoices/<int:pk>/documents/<int:document_id>/", views.sales_invoice_document_delete, name="sales-invoice-document-delete"),
]

purchase_expense_patterns = [
    path("purchase-expenses/", views.purchase_expense_list, name="purchase-expense-list"),
    path("purchase-expenses/<int:pk>/", views.purchase_expense_detail, name="purchase-expense-detail"),
]

# Dropdown endpoints
dropdown_patterns = [
    path("dropdown/companies/", views.companies_dropdown, name="companies-dropdown"),
    path("dropdown/customers/", views.customers_dropdown, name="customers-dropdown"),
    path("dropdown/projects/", views.projects_dropdown, name="projects-dropdown"),
    path("dropdown/suppliers/", views.suppliers_dropdown, name="suppliers-dropdown"),
    path("dropdown/categories/", views.categories_dropdown, name="categories-dropdown"),
    path("dropdown/sub-categories/", views.sub_categories_dropdown, name="sub-categories-dropdown"),
    path("dropdown/products/", views.products_dropdown, name="products-dropdown"),
    path("dropdown/units/", views.units_dropdown, name="units-dropdown"),
    path("dropdown/taxes/", views.taxes_dropdown, name="taxes-dropdown"),
]

# Combine all patterns
urlpatterns = sales_order_patterns + sales_invoice_patterns + purchase_expense_patterns + dropdown_patterns

