from django.urls import path
from . import views

urlpatterns = [
    # CRUD
    path("", views.purchase_expense_list, name="purchase_expense_list"),
    path("<int:pk>/", views.purchase_expense_detail, name="purchase_expense_detail"),
    path("<int:pk>/approve/", views.approve_purchase_expense, name="purchase_expense_approve"),
    path("<int:pk>/reject/", views.reject_purchase_expense, name="purchase_expense_reject"),
    path("approval-level2/", views.purchase_expense_approval_level2_list, name="purchase_expense_approval_level2_list"),
    path("<int:pk>/approve-level2/", views.approve_purchase_expense_level2, name="purchase_expense_approve_level2"),
    path("<int:pk>/reject-level2/", views.reject_purchase_expense_level2, name="purchase_expense_reject_level2"),

    # Dropdowns
    path("dropdowns/companies/", views.companies_dropdown, name="pe_companies_dropdown"),
    path("dropdowns/projects/", views.projects_dropdown, name="pe_projects_dropdown"),
    path("dropdowns/suppliers/", views.suppliers_dropdown, name="pe_suppliers_dropdown"),
    path("dropdowns/expense-categories/", views.expense_categories_dropdown, name="pe_expense_categories_dropdown"),
    path("dropdowns/expense-sub-categories/", views.expense_sub_categories_dropdown, name="pe_expense_sub_categories_dropdown"),
    path("dropdowns/payment-types/", views.payment_types_dropdown, name="pe_payment_types_dropdown"),
    path("dropdowns/products/", views.products_dropdown, name="pe_products_dropdown"),
    path("dropdowns/units/", views.units_dropdown, name="pe_units_dropdown"),
]
