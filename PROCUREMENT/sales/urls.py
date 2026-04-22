from django.urls import path

from . import views

# Sales order endpoints
sales_order_patterns = [
    path("sales-orders/", views.sales_order_list, name="sales-order-list"),
    path("sales-orders/<int:pk>/", views.sales_order_detail, name="sales-order-detail"),
]

# Sales invoice endpoints
sales_invoice_patterns = [
    path("sales-invoices/", views.sales_invoice_list, name="sales-invoice-list"),
    path("sales-invoices/<int:pk>/", views.sales_invoice_detail, name="sales-invoice-detail"),
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


