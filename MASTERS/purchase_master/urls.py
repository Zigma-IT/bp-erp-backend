"""Purchase master URL configuration with a browsable DRF index."""

from django.urls import path
from collections import OrderedDict

from MASTERS.api_router import ExtendedDefaultRouter

from . import views

from .views import (

    ExpenseCategoryCreateAPIView,
    ExpenseCategoryListAPIView,
    ExpenseCategoryDetailAPIView,
    ExpenseCategoryUpdateAPIView,
    ExpenseCategoryDeleteAPIView,
    ExpenseSubCategoryCreateAPIView,
    ExpenseSubCategoryListAPIView,
    ExpenseSubCategoryDetailAPIView,
    ExpenseSubCategoryUpdateAPIView,
    ExpenseSubCategoryDeleteAPIView,
    CustomerCategoryCreateAPIView,
    CustomerCategoryListAPIView,
    CustomerCategoryDetailAPIView,
    CustomerCategoryUpdateAPIView,
    CustomerCategoryDeleteAPIView,
    PaymentCategoryCreateAPIView,
    PaymentCategoryListAPIView,
    PaymentCategoryDetailAPIView,
    PaymentCategoryUpdateAPIView,
    PaymentCategoryDeleteAPIView,

)

router = ExtendedDefaultRouter()

router.extra_api_root_dict = OrderedDict({
    "units": "unit-list",
    "units-create": "unit-create",
    "item-groups": "item-group-list",
    "item-groups-create": "item-group-create",
    "sub-groups": "sub-group-list",
    "sub-groups-create": "sub-group-create",
    "sub-groups-group-dropdown": "sub-group-group-dropdown",
    "categories": "category-list",
    "categories-create": "category-create",
    "categories-group-dropdown": "category-group-dropdown",
    "categories-sub-group-dropdown": "category-sub-group-dropdown",
    "items": "item-list",
    "items-create": "item-create",
    "items-group-dropdown": "item-group-dropdown",
    "items-sub-group-dropdown": "item-sub-group-dropdown",
    "products": "product-list",
    "products-create": "product-create",
    "products-company-dropdown": "product-company-dropdown",
    "products-group-dropdown": "product-group-dropdown",
    "products-group-dropdown-create": "product-group-dropdown-create",
    "products-sub-group-dropdown": "product-sub-group-dropdown",
    "products-sub-group-dropdown-create": "product-sub-group-dropdown-create",
    "boms": "bom-list",
    "boms-create": "bom-create",
    "products-dropdown": "product-dropdown",
    "items-dropdown": "item-dropdown",

    # Expense Category
    "expense-category-list": "expense-category-list",
    "expense-category-create": "expense-category-create",
})

# Unit endpoints
unit_patterns = [
    path('units/', views.unit_list, name='unit-list'),
    path('units/create/', views.create_unit, name='unit-create'),
    path('units/<int:pk>/', views.update_unit, name='unit-update'),
    path('units/<int:pk>/toggle/', views.toggle_unit, name='unit-toggle'),
]

# Item Group endpoints
item_group_patterns = [
    path('item-groups/', views.item_group_list, name='item-group-list'),
    path('item-groups/create/', views.create_item_group, name='item-group-create'),
    path('item-groups/<int:pk>/', views.update_item_group, name='item-group-update'),
    path('item-groups/<int:pk>/toggle/', views.toggle_item_group, name='item-group-toggle'),
]

# Item Sub Group endpoints
sub_group_patterns = [
    path('sub-groups/', views.sub_group_list, name='sub-group-list'),
    path('sub-groups/create/', views.create_sub_group, name='sub-group-create'),
    path('sub-groups/<int:pk>/', views.update_sub_group, name='sub-group-update'),
    path('sub-groups/<int:pk>/toggle/', views.toggle_sub_group, name='sub-group-toggle'),
    path('sub-groups/group-dropdown/', views.group_dropdown, name='sub-group-group-dropdown'),
]

# Category endpoints
category_patterns = [
    path('categories/', views.category_list, name='category-list'),
    path('categories/create/', views.create_category, name='category-create'),
    path('categories/<int:pk>/', views.update_category, name='category-update'),
    path('categories/<int:pk>/toggle/', views.toggle_category, name='category-toggle'),
    path('categories/group-dropdown/', views.group_dropdown, name='category-group-dropdown'),
    path('categories/sub-group-dropdown/', views.sub_group_dropdown, name='category-sub-group-dropdown'),
]

# Item endpoints
item_patterns = [
    path('items/', views.item_list, name='item-list'),
    path('items/create/', views.create_item, name='item-create'),
    path('items/<int:pk>/', views.update_item, name='item-detail'),
    path('items/<int:pk>/toggle/', views.toggle_item, name='item-toggle'),
    path('items/export/', views.export_items, name='item-export'),
    path('items/import/', views.import_items, name='item-import'),
    path('items/group-dropdown/', views.group_dropdown, name='item-group-dropdown'),
    path('items/sub-group-dropdown/', views.sub_group_dropdown, name='item-sub-group-dropdown'),
]

# Product endpoints
product_patterns = [
    path('products/', views.product_list, name='product-list'),
    path('products/create/', views.create_product, name='product-create'),
    path('products/<int:pk>/', views.update_product, name='product-update'),
    path('products/<int:pk>/toggle/', views.toggle_product, name='product-toggle'),
    path('products/company-dropdown/', views.company_dropdown, name='product-company-dropdown'),
    path('products/group-dropdown/', views.product_group_dropdown, name='product-group-dropdown'),
    path('products/group-dropdown/create/', views.create_product_group, name='product-group-dropdown-create'),
    path('products/sub-group-dropdown/', views.product_sub_group_dropdown, name='product-sub-group-dropdown'),
    path('products/sub-group-dropdown/create/', views.create_product_sub_group, name='product-sub-group-dropdown-create'),
    path('products/groups/', views.product_group_management, name='product-group-management'),
    path('products/groups/<int:pk>/delete/', views.delete_product_group, name='product-group-delete'),
    path('products/sub-groups/<int:pk>/delete/', views.delete_product_sub_group, name='product-sub-group-delete'),
]

# BOM endpoints
bom_patterns = [
    path('boms/', views.bom_list, name='bom-list'),
    path('boms/create/', views.create_bom, name='bom-create'),
    path('boms/<int:pk>/view/', views.view_bom, name='bom-view'),
    path('boms/<int:pk>/update/', views.update_bom, name='bom-update'),
    path('boms/<int:pk>/delete/', views.delete_bom, name='bom-delete'),
    path('products-dropdown/', views.product_dropdown, name='product-dropdown'),
    path('items-dropdown/', views.item_dropdown, name='item-dropdown'),
]

# Expense Category endpoints
expense_category_patterns = [
    path(
        "expense-category/create/",
        ExpenseCategoryCreateAPIView.as_view(),
        name="expense-category-create"
    ),
    path(
        "expense-category/list/",
        ExpenseCategoryListAPIView.as_view(),
        name="expense-category-list"
    ),
    path(
        "expense-category/<int:pk>/",
        ExpenseCategoryDetailAPIView.as_view(),
        name="expense-category-detail"
    ),
    path(
        "expense-category/update/<int:pk>/",
        ExpenseCategoryUpdateAPIView.as_view(),
        name="expense-category-update"
    ),
    path(
        "expense-category/delete/<int:pk>/",
        ExpenseCategoryDeleteAPIView.as_view(),
        name="expense-category-delete"
    ),


    path(
        "expense-sub-category/create/",
        ExpenseSubCategoryCreateAPIView.as_view(),
        name="expense-sub-category-create"
    ),

    path(
        "expense-sub-category/list/",
        ExpenseSubCategoryListAPIView.as_view(),
        name="expense-sub-category-list"
    ),

    path(
        "expense-sub-category/<int:pk>/",
        ExpenseSubCategoryDetailAPIView.as_view(),
        name="expense-sub-category-detail"
    ),

    path(
        "expense-sub-category/update/<int:pk>/",
        ExpenseSubCategoryUpdateAPIView.as_view(),
        name="expense-sub-category-update"
    ),

    path(
        "expense-sub-category/delete/<int:pk>/",
        ExpenseSubCategoryDeleteAPIView.as_view(),
        name="expense-sub-category-delete"
    ),


    path(
        "customer-category/create/",
        CustomerCategoryCreateAPIView.as_view(),
        name="customer-category-create"
    ),

    path(
        "customer-category/list/",
        CustomerCategoryListAPIView.as_view(),
        name="customer-category-list"
    ),

    path(
        "customer-category/<int:pk>/",
        CustomerCategoryDetailAPIView.as_view(),
        name="customer-category-detail"
    ),

    path(
        "customer-category/update/<int:pk>/",
        CustomerCategoryUpdateAPIView.as_view(),
        name="customer-category-update"
    ),

    path(
        "customer-category/delete/<int:pk>/",
        CustomerCategoryDeleteAPIView.as_view(),
        name="customer-category-delete"
    ),
       path(
        "payment-category/create/",
        PaymentCategoryCreateAPIView.as_view(),
        name="payment-category-create"
    ),

    path(
        "payment-category/list/",
        PaymentCategoryListAPIView.as_view(),
        name="payment-category-list"
    ),

    path(
        "payment-category/<int:pk>/",
        PaymentCategoryDetailAPIView.as_view(),
        name="payment-category-detail"
    ),

    path(
        "payment-category/update/<int:pk>/",
        PaymentCategoryUpdateAPIView.as_view(),
        name="payment-category-update"
    ),

    path(
        "payment-category/delete/<int:pk>/",
        PaymentCategoryDeleteAPIView.as_view(),
        name="payment-category-delete"
    ),
]

urlpatterns = [
    *unit_patterns,
    *item_group_patterns,
    *sub_group_patterns,
    *category_patterns,
    *item_patterns,
    *product_patterns,
    *bom_patterns,
    *expense_category_patterns,
]
