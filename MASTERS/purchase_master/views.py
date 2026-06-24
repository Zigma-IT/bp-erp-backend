# Units - This file defines the API views for managing units in the purchase_master module of the MASTERS app, including a viewset for CRUD operations on UnitMaster model instances and path-based views for listing units with pagination and search functionality, creating new units, updating existing units, and toggling unit status. The UnitViewSet class provides methods for handling create, update, and delete operations, while the path-based views allow for more customized handling of unit-related API requests, including soft deletion by deactivating units instead of permanently removing them from the database.
import uuid

from typing import Any, cast

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from django.db import connections, transaction
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from io import BytesIO, StringIO
import csv
import re
import logging

from openpyxl import Workbook, load_workbook
import xlrd

from MASTERS.schema_utils import (
    DATATABLE_PARAMETERS,
    SEARCH_PARAMETER,
    query_int_parameter,
)
from common_master.models import Company
from .models import (
    Category,
    ItemGroup,
    ItemMaster,
    ProductCreation,
    ProductCreationGroup,
    ProductCreationSubGroup,
    ProductGroup,
    ProductSubGroup,
    StandardBOM,
    StandardBOMItem,
    SubGroup,
    UnitMaster,
    ExpenseCategory,
    ExpenseSubCategory,
    CustomerCategory,
    PaymentCategory
)
from .serializers import CreateBOMSerializer, StandardBOMSerializer, UnitSerializer , ExpenseCategorySerializer , ExpenseSubCategorySerializer , CustomerCategorySerializer , PaymentCategorySerializer

class UnitViewSet(viewsets.ModelViewSet):
    queryset = UnitMaster.objects.all().order_by('-pk')
    serializer_class = UnitSerializer

    def create(self, request, *args, **kwargs):
        if UnitMaster.objects.filter(unit_name=request.data.get('unit_name')).exists():
            return Response({"error": "Unit already exists"}, status=400)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Soft delete (better for ERP)
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response({"message": "Unit deactivated"})


# Path-based views for units
@api_view(['GET'])
def unit_list(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search = request.GET.get('search[value]', '')

    queryset = UnitMaster.objects.all().order_by('-pk')

    total = queryset.count()

    if search:
        queryset = queryset.filter(
            Q(unit_name__icontains=search) |
            Q(description__icontains=search)
        )

    filtered = queryset.count()
    queryset = queryset[start:start+length]

    serializer = UnitSerializer(queryset, many=True)

    data = []
    for i, item in enumerate(serializer.data, start=1):
        data.append({
            "sno": start + i,
            "unique_id": item["unique_id"],
            "unit_name": item["unit_name"],
            "decimal_points": item["decimal_points"],
            "description": item["description"] or "-",
            "status": "Active" if item["is_active"] else "Inactive",
            "id": item["id"]
        })

    return Response({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": data
    })


@api_view(['POST'])
def create_unit(request):
    # Check if unit already exists
    if UnitMaster.objects.filter(unit_name=request.data.get('unit_name')).exists():
        return Response({"error": "Unit already exists"}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = UnitSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def update_unit(request, pk):
    try:
        obj = UnitMaster.objects.get(pk=pk)
    except UnitMaster.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = UnitSerializer(obj, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Updated successfully", "data": serializer.data})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def toggle_unit(request, pk):
    try:
        obj = UnitMaster.objects.get(pk=pk)
    except UnitMaster.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    
    obj.is_active = not obj.is_active
    obj.save()

    return Response({"message": "Status toggled", "status": obj.is_active})

# Item_groups - This file defines the API views for managing item groups in the purchase_master module of the MASTERS app, including path-based views for listing item groups with pagination and search functionality, creating new item groups, updating existing item groups, and toggling item group status. The views handle HTTP requests and return appropriate responses based on the operations performed on the ItemGroup model, allowing for organized management of item group data within the system.
# LIST (with optional search)
@api_view(['GET'])
def item_group_list(request):
    search = request.GET.get('search', '')
    queryset = ItemGroup.objects.all().order_by("-id")

    if search:
        queryset = queryset.filter(group_name__icontains=search)

    data = list(queryset.values("id", "group_name", "code", "description", "is_active"))

    return Response({
        "status": True,
        "data": data
    })


# CREATE
@api_view(['POST'])
def create_item_group(request):
    group_name = request.data.get('group_name')
    code = request.data.get('code')
    description = request.data.get('description', '')
    is_active = request.data.get('is_active', True)

    # VALIDATION
    if not group_name:
        return Response({"status": False, "message": "Group name is required"}, status=400)

    if not code:
        return Response({"status": False, "message": "Code is required"}, status=400)

    if ItemGroup.objects.filter(group_name=group_name).exists():
        return Response({"status": False, "message": "Group name already exists"}, status=400)

    if ItemGroup.objects.filter(code=code).exists():
        return Response({"status": False, "message": "Code already exists"}, status=400)

    # CREATE
    ItemGroup.objects.create(
        group_name=group_name,
        code=code,
        description=description,
        is_active=is_active
    )

    return Response({
        "status": True,
        "message": "Item Group created successfully"
    })


# UPDATE
@api_view(['PUT'])
def update_item_group(request, pk):
    try:
        obj = ItemGroup.objects.get(id=pk)
    except ItemGroup.DoesNotExist:
        return Response({"status": False, "message": "Item Group not found"}, status=404)

    group_name = request.data.get('group_name')
    code = request.data.get('code')
    description = request.data.get('description', '')
    is_active = request.data.get('is_active', True)

    # VALIDATION
    if not group_name:
        return Response({"status": False, "message": "Group name is required"}, status=400)

    if not code:
        return Response({"status": False, "message": "Code is required"}, status=400)

    if ItemGroup.objects.exclude(id=pk).filter(group_name=group_name).exists():
        return Response({"status": False, "message": "Group name already exists"}, status=400)

    if ItemGroup.objects.exclude(id=pk).filter(code=code).exists():
        return Response({"status": False, "message": "Code already exists"}, status=400)

    # UPDATE
    obj.group_name = group_name
    obj.code = code
    obj.description = description
    obj.is_active = is_active
    obj.save()

    return Response({
        "status": True,
        "message": "Item Group updated successfully"
    })


# TOGGLE ACTIVE STATUS
@api_view(['PATCH'])
def toggle_item_group(request, pk):
    try:
        obj = ItemGroup.objects.get(id=pk)
    except ItemGroup.DoesNotExist:
        return Response({"status": False, "message": "Item Group not found"}, status=404)

    obj.is_active = not obj.is_active
    obj.save()

    return Response({
        "status": True,
        "message": "Status updated successfully",
        "is_active": obj.is_active
    })
#Item_sub_groups - This file defines the API views for managing item sub groups in the purchase_master module of the MASTERS app, including path-based views for listing item sub groups with pagination and search functionality, creating new item sub groups, updating existing item sub groups, and toggling item sub group status. The views handle HTTP requests and return appropriate responses based on the operations performed on the SubGroup model, allowing for organized management of item sub group data within the system.
# LIST
@api_view(['GET'])
def sub_group_list(request):
    search = request.GET.get('search', '')
    group_id = request.GET.get('group_id')
    queryset = SubGroup.objects.select_related("group").all().order_by("-id")

    if group_id:
        queryset = queryset.filter(group_id=group_id)

    if search:
        queryset = queryset.filter(sub_group_name__icontains=search)

    data = [
        {
            "id": obj.pk,
            "sub_group_name": obj.sub_group_name,
            "sub_group_code": obj.sub_group_code,
            "group_name": obj.group.group_name,
            "group_code": obj.group.code,
            "group_id": obj.group_id,
            "description": obj.description,
            "is_active": obj.is_active,
        }
        for obj in queryset
    ]

    return Response({
        "status": True,
        "data": data
    })


# CREATE
@api_view(['POST'])
def create_sub_group(request):
    group_id = request.data.get('group_id')
    name = request.data.get('sub_group_name')
    code = request.data.get('sub_group_code')
    description = request.data.get('description', '')
    is_active = request.data.get('is_active', True)

    if not group_id:
        return Response({"status": False, "message": "Group is required"}, status=400)

    if not name:
        return Response({"status": False, "message": "Sub group name is required"}, status=400)

    if not code:
        return Response({"status": False, "message": "Sub group code is required"}, status=400)

    try:
        group = ItemGroup.objects.get(id=group_id)
    except ItemGroup.DoesNotExist:
        return Response({"status": False, "message": "Invalid group"}, status=400)

    if SubGroup.objects.filter(sub_group_name=name, group=group).exists():
        return Response({"status": False, "message": "Sub group already exists in this group"}, status=400)

    if SubGroup.objects.filter(sub_group_code=code).exists():
        return Response({"status": False, "message": "Sub group code already exists"}, status=400)

    SubGroup.objects.create(
        group=group,
        sub_group_name=name,
        sub_group_code=code,
        description=description,
        is_active=is_active,
    )

    return Response({
        "status": True,
        "message": "Sub Group created successfully"
    })


# UPDATE
@api_view(['PUT'])
def update_sub_group(request, pk):
    group_id = request.data.get('group_id')
    name = request.data.get('sub_group_name')
    code = request.data.get('sub_group_code')
    description = request.data.get('description', '')
    is_active = request.data.get('is_active', True)

    if not group_id:
        return Response({"status": False, "message": "Group is required"}, status=400)

    if not name:
        return Response({"status": False, "message": "Sub group name is required"}, status=400)

    if not code:
        return Response({"status": False, "message": "Sub group code is required"}, status=400)

    try:
        obj = SubGroup.objects.get(id=pk)
    except SubGroup.DoesNotExist:
        return Response({"status": False, "message": "Sub group not found"}, status=404)

    try:
        group = ItemGroup.objects.get(id=group_id)
    except ItemGroup.DoesNotExist:
        return Response({"status": False, "message": "Invalid group"}, status=400)

    if SubGroup.objects.exclude(id=pk).filter(sub_group_name=name, group=group).exists():
        return Response({"status": False, "message": "Sub group already exists in this group"}, status=400)

    if SubGroup.objects.exclude(id=pk).filter(sub_group_code=code).exists():
        return Response({"status": False, "message": "Sub group code already exists"}, status=400)

    obj.group = group
    obj.sub_group_name = name
    obj.sub_group_code = code
    obj.description = description
    obj.is_active = is_active
    obj.save()

    return Response({
        "status": True,
        "message": "Sub Group updated successfully"
    })


# TOGGLE
@api_view(['PATCH'])
def toggle_sub_group(request, pk):
    try:
        obj = SubGroup.objects.get(id=pk)
    except SubGroup.DoesNotExist:
        return Response({"status": False, "message": "Sub group not found"}, status=404)

    obj.is_active = not obj.is_active
    obj.save()

    return Response({
        "status": True,
        "message": "Status updated",
        "is_active": obj.is_active
    })


# DROPDOWN (for create page)
@api_view(['GET'])
def sub_group_group_dropdown(request):
    groups = list(
        ItemGroup.objects.filter(is_active=True)
        .order_by("group_name")
        .values("id", "group_name", "code")
    )

    return Response({
        "status": True,
        "data": groups
    })
# Item_category's - This file defines the API views for managing item categories in the purchase_master module of the MASTERS app, including path-based views for listing item categories with pagination and search functionality, creating new item categories, updating existing item categories, and toggling item category status. The views handle HTTP requests and return appropriate responses based on the operations performed on the Category model, allowing for organized management of item category data within the system. Additionally, there are views for retrieving dropdown data for groups and sub groups to facilitate category creation and updates.
# LIST
@api_view(['GET'])
def category_list(request):
    search = request.GET.get('search', '')
    group_id = request.GET.get('group_id')
    sub_group_id = request.GET.get('sub_group_id')

    queryset = Category.objects.select_related('group', 'sub_group').all()

    if group_id:
        queryset = queryset.filter(group_id=group_id)

    if sub_group_id:
        queryset = queryset.filter(sub_group_id=sub_group_id)

    if search:
        queryset = queryset.filter(category_name__icontains=search)

    data = []
    for obj in queryset:
        data.append({
            "id": obj.pk,
            "category_name": obj.category_name,
            "category_code": obj.category_code,
            "group_name": obj.group.group_name,
            "group_code": obj.group.code,
            "sub_group_name": obj.sub_group.sub_group_name,
            "sub_group_code": obj.sub_group.sub_group_code,
            "description": obj.description,
            "is_active": obj.is_active
        })

    return Response({
        "status": True,
        "data": data
    })


# CREATE
@api_view(['POST'])
def create_category(request):
    group_id = request.data.get('group_id')
    sub_group_id = request.data.get('sub_group_id')
    name = request.data.get('category_name')
    code = request.data.get('category_code')
    description = request.data.get('description', '')
    is_active = request.data.get('is_active', True)

    if not group_id:
        return Response({"status": False, "message": "Group is required"}, status=400)

    if not sub_group_id:
        return Response({"status": False, "message": "Sub group is required"}, status=400)

    if not name:
        return Response({"status": False, "message": "Category name is required"}, status=400)

    if not code:
        return Response({"status": False, "message": "Category code is required"}, status=400)

    try:
        group = ItemGroup.objects.get(id=group_id)
    except ItemGroup.DoesNotExist:
        return Response({"status": False, "message": "Invalid group"}, status=400)

    try:
        sub_group = SubGroup.objects.get(id=sub_group_id, group=group)
    except SubGroup.DoesNotExist:
        return Response({"status": False, "message": "Invalid sub group for selected group"}, status=400)

    if Category.objects.filter(category_name=name, sub_group=sub_group).exists():
        return Response({"status": False, "message": "Category already exists in this sub group"}, status=400)

    if Category.objects.filter(category_code=code).exists():
        return Response({"status": False, "message": "Category code already exists"}, status=400)

    Category.objects.create(
        group=group,
        sub_group=sub_group,
        category_name=name,
        category_code=code,
        description=description,
        is_active=is_active
    )

    return Response({
        "status": True,
        "message": "Category created successfully"
    })


# UPDATE
@api_view(['PUT'])
def update_category(request, pk):
    try:
        obj = Category.objects.get(id=pk)
    except Category.DoesNotExist:
        return Response({"status": False, "message": "Category not found"}, status=404)

    group_id = request.data.get('group_id')
    sub_group_id = request.data.get('sub_group_id')
    name = request.data.get('category_name')
    code = request.data.get('category_code')
    description = request.data.get('description', '')
    is_active = request.data.get('is_active', True)

    if not group_id or not sub_group_id:
        return Response({"status": False, "message": "Group & Sub group required"}, status=400)

    try:
        group = ItemGroup.objects.get(id=group_id)
        sub_group = SubGroup.objects.get(id=sub_group_id, group=group)
    except (ItemGroup.DoesNotExist, SubGroup.DoesNotExist):
        return Response({"status": False, "message": "Invalid group/sub group"}, status=400)

    if Category.objects.exclude(id=pk).filter(category_name=name, sub_group=sub_group).exists():
        return Response({"status": False, "message": "Category already exists"}, status=400)

    if Category.objects.exclude(id=pk).filter(category_code=code).exists():
        return Response({"status": False, "message": "Category code already exists"}, status=400)

    obj.group = group
    obj.sub_group = sub_group
    obj.category_name = name
    obj.category_code = code
    obj.description = description
    obj.is_active = is_active
    obj.save()

    return Response({
        "status": True,
        "message": "Category updated successfully"
    })


# TOGGLE
@api_view(['PATCH'])
def toggle_category(request, pk):
    try:
        obj = Category.objects.get(id=pk)
    except Category.DoesNotExist:
        return Response({"status": False, "message": "Category not found"}, status=404)

    obj.is_active = not obj.is_active
    obj.save()

    return Response({
        "status": True,
        "message": "Status updated",
        "is_active": obj.is_active
    })


# GROUP DROPDOWN
@api_view(['GET'])
def category_group_dropdown(request):
    data = ItemGroup.objects.filter(is_active=True).values('id', 'group_name', 'code')
    return Response({"status": True, "data": list(data)})


# SUB GROUP DROPDOWN (based on group)
@api_view(['GET'])
def category_sub_group_dropdown(request):
    group_id = request.GET.get('group_id')

    queryset = SubGroup.objects.filter(is_active=True)

    if group_id:
        queryset = queryset.filter(group_id=group_id)

    data = queryset.values('id', 'sub_group_name', 'sub_group_code')

    return Response({
        "status": True,
        "data": list(data)
    })
# Item_names/code - This file defines the API views for managing item names and codes in the purchase_master module of the MASTERS app, including path-based views for listing items with pagination and search functionality, creating new items, updating existing items, and toggling item status. The views handle HTTP requests and return appropriate responses based on the operations performed on the ItemMaster model, allowing for organized management of item data within the system. Additionally, there are views for retrieving dropdown data for groups, sub groups, and categories to facilitate item creation and updates.
# LIST
@api_view(['GET'])
def item_list_legacy(request):
    group_id = request.GET.get('group_id')
    sub_group_id = request.GET.get('sub_group_id')
    category_id = request.GET.get('category_id')
    search = request.GET.get('search', '')

    queryset = ItemMaster.objects.select_related(
        'group', 'sub_group', 'category', 'unit'
    ).all()

    if group_id:
        queryset = queryset.filter(group_id=group_id)

    if sub_group_id:
        queryset = queryset.filter(sub_group_id=sub_group_id)

    if category_id:
        queryset = queryset.filter(category_id=category_id)

    if search:
        queryset = queryset.filter(item_name__icontains=search)

    data = []
    for obj in queryset:
        data.append({
            "id": obj.pk,
            "item_name": obj.item_name,
            "item_code": obj.item_code,
            "group_name": obj.group.group_name,
            "sub_group_name": obj.sub_group.sub_group_name,
            "category_name": obj.category.category_name,
            "unit_name": obj.unit.unit_name if obj.unit else None,
            "description": obj.description,
            "is_active": obj.is_active
        })

    return Response({"status": True, "data": data})


# CREATE
@api_view(['POST'])
def create_item_legacy(request):
    group_id = request.data.get('group_id')
    sub_group_id = request.data.get('sub_group_id')
    category_id = request.data.get('category_id')
    unit_id = request.data.get('unit_id')
    item_name = request.data.get('item_name')

    if not all([group_id, sub_group_id, category_id, item_name]):
        return Response({"status": False, "message": "Required fields missing"}, status=400)

    group = ItemGroup.objects.get(id=group_id)
    sub_group = SubGroup.objects.get(id=sub_group_id, group=group)
    category = Category.objects.get(id=category_id, sub_group=sub_group)
    unit = UnitMaster.objects.get(id=unit_id) if unit_id else None

    # 🔥 AUTO CODE
    item_code = generate_item_code(group, sub_group, category)

    ItemMaster.objects.create(
        group=group,
        sub_group=sub_group,
        category=category,
        unit=unit,
        item_name=item_name,
        item_code=item_code,
        reorder_level=request.data.get('reorder_level', 0),
        reorder_qty=request.data.get('reorder_qty', 0),
        purchase_lead_time=request.data.get('purchase_lead_time', 0),
        unit_price=request.data.get('unit_price', 0),
        hsn_code=request.data.get('hsn_code'),
        tolerance=request.data.get('tolerance', 0),
        tax=request.data.get('tax', 0),
        description=request.data.get('description'),
        is_active=request.data.get('is_active', True)
    )

    return Response({
        "status": True,
        "message": "Item created successfully",
        "item_code": item_code
    })


# TOGGLE
@api_view(['PATCH'])
def toggle_item_legacy(request, pk):
    obj = ItemMaster.objects.get(id=pk)
    obj.is_active = not obj.is_active
    obj.save()

    return Response({"status": True})

def generate_item_code(group, sub_group, category):
    prefix = f"{group.code}-{sub_group.sub_group_code}-{category.category_code}"

    last_item = ItemMaster.objects.filter(
        group=group,
        sub_group=sub_group,
        category=category
    ).order_by('-id').first()

    if last_item:
        last_number = int(last_item.item_code.split('-')[-1])
        new_number = last_number + 1
    else:
        new_number = 1

    return f"{prefix}-{str(new_number).zfill(5)}"

# LIST
@api_view(['GET'])
def item_list(request):
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    group_id = request.GET.get('group_id')
    sub_group_id = request.GET.get('sub_group_id')
    category_id = request.GET.get('category_id')
    search = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', 'item_code')
    order = request.GET.get('order', 'asc')

    allowed_sort = {
        'item_code': 'item_code',
        'item_name': 'item_name',
        'category': 'category__category_name',
        'sub_group': 'sub_group__sub_group_name',
        'group': 'group__group_name',
        'uom': 'unit__unit_name',
        'unit_price': 'unit_price',
        'gst': 'tax',
        'status': 'is_active'
    }

    queryset = ItemMaster.objects.select_related(
        'group', 'sub_group', 'category', 'unit'
    ).all()

    if group_id:
        queryset = queryset.filter(group_id=group_id)

    if sub_group_id:
        queryset = queryset.filter(sub_group_id=sub_group_id)

    if category_id:
        queryset = queryset.filter(category_id=category_id)

    if search:
        queryset = queryset.filter(
            Q(item_name__icontains=search) |
            Q(item_code__icontains=search)
        )

    total = queryset.count()
    sort_field = allowed_sort.get(sort_by, 'item_code')
    if order == 'desc':
        sort_field = f'-{sort_field}'

    queryset = queryset.order_by(sort_field)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = queryset[start:end]

    data = []
    for obj in page_items:
        data.append({
            'id': obj.pk,
            'item_name': obj.item_name,
            'item_code': obj.item_code,
            'group_id': obj.group_id,
            'group_name': obj.group.group_name,
            'sub_group_id': obj.sub_group_id,
            'sub_group_name': obj.sub_group.sub_group_name,
            'category_id': obj.category_id,
            'category_name': obj.category.category_name,
            'unit_id': obj.unit_id,
            'unit_name': obj.unit.unit_name if obj.unit else None,
            'reorder_level': obj.reorder_level,
            'reorder_qty': obj.reorder_qty,
            'purchase_lead_time': obj.purchase_lead_time,
            'unit_price': float(obj.unit_price or 0),
            'gst': float(obj.tax or 0),
            'hsn_code': obj.hsn_code,
            'tolerance': float(obj.tolerance or 0),
            'description': obj.description,
            'status': 'Active' if obj.is_active else 'Inactive',
            'is_active': obj.is_active,
        })

    return Response({
        'status': True,
        'data': data,
        'page': page,
        'page_size': page_size,
        'total': total,
        'pages': max(1, (total + page_size - 1) // page_size),
    })


# CREATE
@api_view(['POST'])
def create_item(request):
    group_id = request.data.get('group_id')
    sub_group_id = request.data.get('sub_group_id')
    category_id = request.data.get('category_id')
    unit_id = request.data.get('unit_id')
    item_name = request.data.get('item_name')

    if not all([group_id, sub_group_id, category_id, item_name]):
        return Response({'status': False, 'message': 'Required fields missing'}, status=400)

    try:
        group = ItemGroup.objects.get(id=group_id)
        sub_group = SubGroup.objects.get(id=sub_group_id, group=group)
        category = Category.objects.get(id=category_id, sub_group=sub_group)
    except ItemGroup.DoesNotExist:
        return Response({'status': False, 'message': 'Item group not found'}, status=404)
    except SubGroup.DoesNotExist:
        return Response({'status': False, 'message': 'Item sub-group not found'}, status=404)
    except Category.DoesNotExist:
        return Response({'status': False, 'message': 'Category not found'}, status=404)

    if ItemMaster.objects.filter(
        group=group,
        sub_group=sub_group,
        category=category,
        item_name__iexact=item_name.strip()
    ).exists():
        return Response({'status': False, 'message': 'Duplicate item exists for selected group, sub group, category and item name'}, status=400)

    unit = UnitMaster.objects.get(id=unit_id) if unit_id else None
    item_code = generate_item_code(group, sub_group, category)

    ItemMaster.objects.create(
        group=group,
        sub_group=sub_group,
        category=category,
        unit=unit,
        item_name=item_name.strip(),
        item_code=item_code,
        reorder_level=request.data.get('reorder_level', 0),
        reorder_qty=request.data.get('reorder_qty', 0),
        purchase_lead_time=request.data.get('purchase_lead_time', 0),
        unit_price=request.data.get('unit_price', 0),
        hsn_code=request.data.get('hsn_code'),
        tolerance=request.data.get('tolerance', 0),
        tax=request.data.get('tax', 0),
        description=request.data.get('description'),
        is_active=request.data.get('is_active', True)
    )

    return Response({'status': True, 'message': 'Item created successfully', 'item_code': item_code})


@api_view(['GET', 'PUT'])
def update_item(request, pk):
    try:
        obj = ItemMaster.objects.select_related('group', 'sub_group', 'category', 'unit').get(id=pk)
    except ItemMaster.DoesNotExist:
        return Response({'status': False, 'message': 'Item not found'}, status=404)

    if request.method == 'GET':
        return Response({'status': True, 'data': {
            'id': obj.pk,
            'group_id': obj.group_id,
            'sub_group_id': obj.sub_group_id,
            'category_id': obj.category_id,
            'unit_id': obj.unit_id,
            'item_name': obj.item_name,
            'item_code': obj.item_code,
            'reorder_level': obj.reorder_level,
            'reorder_qty': obj.reorder_qty,
            'purchase_lead_time': obj.purchase_lead_time,
            'unit_price': float(obj.unit_price or 0),
            'hsn_code': obj.hsn_code,
            'tolerance': float(obj.tolerance or 0),
            'gst': float(obj.tax or 0),
            'description': obj.description,
            'is_active': obj.is_active,
            'group_name': obj.group.group_name,
            'sub_group_name': obj.sub_group.sub_group_name,
            'category_name': obj.category.category_name,
            'unit_name': obj.unit.unit_name if obj.unit else None,
        }})

    group_id = request.data.get('group_id')
    sub_group_id = request.data.get('sub_group_id')
    category_id = request.data.get('category_id')
    unit_id = request.data.get('unit_id')
    item_name = request.data.get('item_name')

    if not all([group_id, sub_group_id, category_id, item_name]):
        return Response({'status': False, 'message': 'Required fields missing'}, status=400)

    try:
        group = ItemGroup.objects.get(id=group_id)
        sub_group = SubGroup.objects.get(id=sub_group_id, group=group)
        category = Category.objects.get(id=category_id, sub_group=sub_group)
    except ItemGroup.DoesNotExist:
        return Response({'status': False, 'message': 'Item group not found'}, status=404)
    except SubGroup.DoesNotExist:
        return Response({'status': False, 'message': 'Item sub-group not found'}, status=404)
    except Category.DoesNotExist:
        return Response({'status': False, 'message': 'Category not found'}, status=404)

    if ItemMaster.objects.exclude(id=obj.id).filter(
        group=group,
        sub_group=sub_group,
        category=category,
        item_name__iexact=item_name.strip()
    ).exists():
        return Response({'status': False, 'message': 'Duplicate item exists for selected group, sub group, category and item name'}, status=400)

    if obj.group_id != group.id or obj.sub_group_id != sub_group.id or obj.category_id != category.id:
        obj.item_code = generate_item_code(group, sub_group, category)

    obj.group = group
    obj.sub_group = sub_group
    obj.category = category
    obj.unit = UnitMaster.objects.get(id=unit_id) if unit_id else None
    obj.item_name = item_name.strip()
    obj.reorder_level = request.data.get('reorder_level', obj.reorder_level)
    obj.reorder_qty = request.data.get('reorder_qty', obj.reorder_qty)
    obj.purchase_lead_time = request.data.get('purchase_lead_time', obj.purchase_lead_time)
    obj.unit_price = request.data.get('unit_price', obj.unit_price)
    obj.hsn_code = request.data.get('hsn_code', obj.hsn_code)
    obj.tolerance = request.data.get('tolerance', obj.tolerance)
    obj.tax = request.data.get('tax', obj.tax)
    obj.description = request.data.get('description', obj.description)
    obj.is_active = request.data.get('is_active', obj.is_active)
    obj.save()

    return Response({'status': True, 'message': 'Item updated successfully', 'item_code': obj.item_code})


# EXPORT
@api_view(['GET'])
def export_items(request):
    group_id = request.GET.get('group_id')
    sub_group_id = request.GET.get('sub_group_id')
    category_id = request.GET.get('category_id')
    search = request.GET.get('search', '')

    queryset = ItemMaster.objects.select_related('group', 'sub_group', 'category', 'unit').all()

    if group_id:
        queryset = queryset.filter(group_id=group_id)

    if sub_group_id:
        queryset = queryset.filter(sub_group_id=sub_group_id)

    if category_id:
        queryset = queryset.filter(category_id=category_id)

    if search:
        queryset = queryset.filter(
            Q(item_name__icontains=search) |
            Q(item_code__icontains=search)
        )

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Items'

    headers = [
        'Group Code',
        'Group Name',
        'Sub Group Code',
        'Sub Group Name',
        'Category Code',
        'Category Name',
        'Item Code',
        'Item Name',
        'Unit Name',
        'Reorder Level',
        'Reorder Qty',
        'Purchase Lead Time',
        'Unit Price',
        'HSN Code',
        'Tolerance',
        'GST',
        'Description',
        'Status',
    ]
    worksheet.append(headers)

    for obj in queryset.order_by('item_code'):
        worksheet.append([
            obj.group.code,
            obj.group.group_name,
            obj.sub_group.sub_group_code,
            obj.sub_group.sub_group_name,
            obj.category.category_code,
            obj.category.category_name,
            obj.item_code,
            obj.item_name,
            obj.unit.unit_name if obj.unit else '',
            obj.reorder_level,
            obj.reorder_qty,
            obj.purchase_lead_time,
            float(obj.unit_price or 0),
            obj.hsn_code or '',
            float(obj.tolerance or 0),
            float(obj.tax or 0),
            obj.description or '',
            'Active' if obj.is_active else 'Inactive',
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="item_master_export.xlsx"'
    workbook.save(response)
    return response


def resolve_group(value: str):
    if not value:
        return None
    value = value.strip()
    group = ItemGroup.objects.filter(code__iexact=value).first()
    if group:
        return group
    return ItemGroup.objects.filter(group_name__iexact=value).first()


def resolve_sub_group(group: ItemGroup, value: str):
    if not group or not value:
        return None
    value = value.strip()
    sub_group = SubGroup.objects.filter(group=group, sub_group_code__iexact=value).first()
    if sub_group:
        return sub_group
    return SubGroup.objects.filter(group=group, sub_group_name__iexact=value).first()


def resolve_category(sub_group: SubGroup, value: str):
    if not sub_group or not value:
        return None
    value = value.strip()
    category = Category.objects.filter(sub_group=sub_group, category_code__iexact=value).first()
    if category:
        return category
    return Category.objects.filter(sub_group=sub_group, category_name__iexact=value).first()


@api_view(['POST'])
def import_items(request):
    workbook_file = request.FILES.get('file')
    if not workbook_file:
        return Response({'status': False, 'message': 'No file provided'}, status=400)

    filename = workbook_file.name.lower()
    workbook_data = workbook_file.read()
    rows = []

    def normalize_header(header_value: str) -> str:
        return re.sub(r'[^a-z0-9_]', '', header_value.strip().lower().replace(' ', '_'))

    def parse_csv_text(data_bytes: bytes):
        text = data_bytes.decode('utf-8', errors='replace')
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            return []
        try:
            dialect = csv.Sniffer().sniff(lines[0])
        except Exception:
            dialect = csv.excel
        return [row for row in csv.reader(lines, dialect)]

    def parse_html_table(data_bytes: bytes):
        text = data_bytes.decode('utf-8', errors='replace')
        # crude but effective extraction of table rows and cells
        rows = []
        for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', text, flags=re.S | re.I):
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, flags=re.S | re.I)
            cleaned = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            if cleaned:
                rows.append(cleaned)
        return rows

    def is_text_content(data_bytes: bytes) -> bool:
        try:
            text = data_bytes.decode('utf-8')
            return bool(text.strip())
        except Exception:
            return False

    logger = logging.getLogger(__name__)
    try:
        workbook_format = xlrd.inspect_format(content=workbook_data)
        if filename.endswith('.xls') or workbook_format == 'xls':
            if workbook_data[:2] == b'PK' or workbook_format == 'xlsx':
                workbook = load_workbook(filename=BytesIO(workbook_data), data_only=True)
                sheet = workbook.active
                rows = list(sheet.iter_rows(values_only=True))
            else:
                try:
                    workbook = xlrd.open_workbook(file_contents=workbook_data, ignore_workbook_corruption=True)
                    sheet = workbook.sheet_by_index(0)
                    rows = [[sheet.cell_value(row_idx, col_idx) for col_idx in range(sheet.ncols)] for row_idx in range(sheet.nrows)]
                except Exception as e_xlrd:
                    logger.exception('xlrd failed to open workbook')
                    # try HTML table fallback
                    if is_text_content(workbook_data):
                        text = workbook_data.decode('utf-8', errors='replace')
                        if '<table' in text.lower() or '<tr' in text.lower():
                            rows = parse_html_table(workbook_data)
                        else:
                            # try CSV fallback
                            rows = parse_csv_text(workbook_data)
                    else:
                        raise
        else:
            workbook = load_workbook(filename=BytesIO(workbook_data), data_only=True)
            sheet = workbook.active
            rows = list(sheet.iter_rows(values_only=True))
    except Exception as error:
        logger.exception('Failed to parse uploaded workbook')
        return Response({'status': False, 'message': f'Invalid Excel file: {repr(error)}'}, status=400)

    # Parsing already handled above; `rows` should now contain the spreadsheet data.

    if len(rows) < 2:
        return Response({'status': False, 'message': 'Excel file does not contain any data rows'}, status=400)

    def empty_headers():
        return {
            'item_code': None,
            'group_code': None,
            'group_name': None,
            'sub_group_code': None,
            'sub_group_name': None,
            'category_code': None,
            'category_name': None,
            'item_name': None,
            'unit_name': None,
            'reorder_level': None,
            'reorder_qty': None,
            'purchase_lead_time': None,
            'unit_price': None,
            'hsn_code': None,
            'tolerance': None,
            'gst': None,
            'tax': None,
            'description': None,
            'status': None,
        }

    def map_headers(row):
        header_row = [normalize_header(str(cell)) if cell is not None else '' for cell in row]
        mapped_headers = empty_headers()

        for index, header in enumerate(header_row):
            if header in mapped_headers:
                mapped_headers[header] = index
                continue

            # Heuristic mappings for common header variations
            if 'item' in header and 'code' in header:
                mapped_headers['item_code'] = index
                continue
            if 'item' in header and 'name' in header:
                mapped_headers['item_name'] = index
                continue
            if header in ('item', 'itemname', 'item_name'):
                mapped_headers['item_name'] = index
                continue

            if 'sub' in header and 'group' in header and 'code' in header:
                mapped_headers['sub_group_code'] = index
                continue
            if 'sub' in header and 'group' in header and 'name' in header:
                mapped_headers['sub_group_name'] = index
                continue
            if 'sub' in header and 'group' in header and header.count('_') == 1:
                # fallback if header like 'sub_group'
                mapped_headers['sub_group_name'] = index
                continue

            if 'group' in header and 'code' in header:
                mapped_headers['group_code'] = index
                continue
            if 'group' in header and 'name' in header:
                mapped_headers['group_name'] = index
                continue
            if header == 'group':
                mapped_headers['group_name'] = index
                continue

            if 'category' in header and 'code' in header:
                mapped_headers['category_code'] = index
                continue
            if 'category' in header and 'name' in header:
                mapped_headers['category_name'] = index
                continue
            if header == 'category':
                mapped_headers['category_name'] = index
                continue

            # small helpful mappings
            if header in ('uom', 'unit'):
                mapped_headers['unit_name'] = index
                continue
            if 'gst' in header:
                mapped_headers['gst'] = index
                continue
            if header == 'status' or 'active' in header:
                mapped_headers['status'] = index
                continue

        return mapped_headers

    def has_required_headers(mapped_headers):
        return not (
            mapped_headers['item_name'] is None
            or (mapped_headers['group_code'] is None and mapped_headers['group_name'] is None)
            or (mapped_headers['sub_group_code'] is None and mapped_headers['sub_group_name'] is None)
            or (mapped_headers['category_code'] is None and mapped_headers['category_name'] is None)
        )

    header_index = None
    headers = empty_headers()
    for candidate_index, row in enumerate(rows[:10]):
        candidate_headers = map_headers(row)
        if has_required_headers(candidate_headers):
            header_index = candidate_index
            headers = candidate_headers
            break

    if header_index is None:
        return Response({'status': False, 'message': 'Required columns missing. Need Group, Sub Group, Category and Item Name columns.'}, status=400)

    if len(rows) <= header_index + 1:
        return Response({'status': False, 'message': 'Excel file does not contain any data rows'}, status=400)

    created = 0
    updated = 0
    skipped = 0
    errors = []

    for row_number, row in enumerate(rows[header_index + 1:], start=header_index + 2):
        if row is None or all(cell is None for cell in row):
            continue

        row_data = {key: (row[index] if index is not None and index < len(row) else None) for key, index in headers.items()}
        group_value = str(row_data.get('group_code') or row_data.get('group_name') or '').strip()
        sub_group_value = str(row_data.get('sub_group_code') or row_data.get('sub_group_name') or '').strip()
        category_value = str(row_data.get('category_code') or row_data.get('category_name') or '').strip()
        item_name = str(row_data.get('item_name') or '').strip()
        item_code = str(row_data.get('item_code') or '').strip()

        if not group_value or not sub_group_value or not category_value or not item_name:
            errors.append({'row': row_number, 'message': 'Missing required classification or item name'})
            continue

        group = resolve_group(group_value)
        if not group:
            errors.append({'row': row_number, 'message': f'Group not found: {group_value}'})
            continue

        sub_group = resolve_sub_group(group, sub_group_value)
        if not sub_group:
            errors.append({'row': row_number, 'message': f'Sub Group not found for group {group.group_name}: {sub_group_value}'})
            continue

        category = resolve_category(sub_group, category_value)
        if not category:
            errors.append({'row': row_number, 'message': f'Category not found for sub group {sub_group.sub_group_name}: {category_value}'})
            continue

        unit_name = str(row_data.get('unit_name') or '').strip()
        unit = UnitMaster.objects.filter(unit_name__iexact=unit_name).first() if unit_name else None

        existing_item = None
        if item_code:
            existing_item = ItemMaster.objects.filter(item_code__iexact=item_code).first()
        if existing_item is None:
            existing_item = ItemMaster.objects.filter(
                group=group,
                sub_group=sub_group,
                category=category,
                item_name__iexact=item_name,
            ).first()

        try:
            item_values = {
                'group': group,
                'sub_group': sub_group,
                'category': category,
                'unit': unit,
                'item_name': item_name,
                'reorder_level': int(row_data.get('reorder_level') or 0),
                'reorder_qty': int(row_data.get('reorder_qty') or 0),
                'purchase_lead_time': int(row_data.get('purchase_lead_time') or 0),
                'unit_price': float(row_data.get('unit_price') or 0),
                'hsn_code': str(row_data.get('hsn_code') or '').strip() or None,
                'tolerance': float(row_data.get('tolerance') or row_data.get('gst') or 0),
                'tax': float(row_data.get('tax') or row_data.get('gst') or 0),
                'description': str(row_data.get('description') or '').strip() or None,
                'is_active': str(row_data.get('status') or '').strip().lower() not in ('inactive', 'no', 'false', '0'),
            }

            if existing_item:
                for field, value in item_values.items():
                    setattr(existing_item, field, value)
                existing_item.save()
                updated += 1
                continue

            ItemMaster.objects.create(
                **item_values,
                item_code=generate_item_code(group, sub_group, category),
            )
            created += 1
        except Exception as exc:
            errors.append({'row': row_number, 'message': f'Failed to save item: {exc}'})

    return Response({'status': True, 'created': created, 'updated': updated, 'skipped': skipped, 'errors': errors})


# TOGGLE
@api_view(['PATCH'])
def toggle_item(request, pk):
    obj = ItemMaster.objects.get(id=pk)
    obj.is_active = not obj.is_active
    obj.save()

    return Response({"status": True})
# ── Product Creation views ────────────────────────────────────────────────────
# Groups/sub-groups are stored in brand-new isolated tables
# (product_creation_group / product_creation_subgroup).
# There is NO foreign-key link to ItemGroup, SubGroup, ProductGroup, or any other master.

@api_view(['GET'])
def product_list(request):
    group_id = request.GET.get('group_id')
    sub_group_id = request.GET.get('sub_group_id')
    company_id = request.GET.get('company_id')
    search = request.GET.get('search', '')

    queryset = ProductCreation.objects.select_related(
        'company', 'product_group', 'product_sub_group'
    ).all()

    if group_id:
        queryset = queryset.filter(product_group_id=group_id)
    if sub_group_id:
        queryset = queryset.filter(product_sub_group_id=sub_group_id)
    if company_id:
        queryset = queryset.filter(company_id=company_id)
    if search:
        queryset = queryset.filter(product_name__icontains=search)

    data = [
        {
            "id": obj.pk,
            "company_name": obj.company.name if obj.company else None,
            "group_name": obj.product_group.name if obj.product_group else None,
            "sub_group_name": obj.product_sub_group.name if obj.product_sub_group else None,
            "product_name": obj.product_name,
            "description": obj.description,
            "is_active": obj.is_active,
        }
        for obj in queryset
    ]
    return Response({"status": True, "data": data})


@api_view(['POST'])
def create_product(request):
    company_id = request.data.get('company_id')
    group_id = request.data.get('group_id')
    sub_group_id = request.data.get('sub_group_id')
    product_name = request.data.get('product_name')

    if not company_id:
        return Response({"status": False, "message": "Company required"}, status=400)
    if not product_name:
        return Response({"status": False, "message": "Product name required"}, status=400)

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response({"status": False, "message": "Invalid company"}, status=400)

    product_group = None
    if group_id:
        try:
            product_group = ProductCreationGroup.objects.get(id=group_id)
        except ProductCreationGroup.DoesNotExist:
            return Response({"status": False, "message": "Invalid group"}, status=400)

    product_sub_group = None
    if sub_group_id:
        try:
            product_sub_group = ProductCreationSubGroup.objects.get(id=sub_group_id, group=product_group)
        except ProductCreationSubGroup.DoesNotExist:
            return Response({"status": False, "message": "Invalid sub group for selected group"}, status=400)

    if ProductCreation.objects.filter(product_name=product_name, company=company).exists():
        return Response({"status": False, "message": "Product already exists"}, status=400)

    ProductCreation.objects.create(
        company=company,
        product_group=product_group,
        product_sub_group=product_sub_group,
        product_name=product_name,
        description=request.data.get('description'),
        is_active=request.data.get('is_active', True),
    )
    return Response({"status": True, "message": "Product created successfully"})


@api_view(['PUT'])
def update_product(request, pk):
    try:
        obj = ProductCreation.objects.get(id=pk)
    except ProductCreation.DoesNotExist:
        return Response({"status": False, "message": "Product not found"}, status=404)

    obj.product_name = request.data.get('product_name', obj.product_name)
    obj.description = request.data.get('description', obj.description)
    obj.is_active = request.data.get('is_active', obj.is_active)

    group_id = request.data.get('group_id')
    sub_group_id = request.data.get('sub_group_id')

    if group_id is not None:
        if group_id:
            try:
                obj.product_group = ProductCreationGroup.objects.get(id=group_id)
            except ProductCreationGroup.DoesNotExist:
                return Response({"status": False, "message": "Invalid group"}, status=400)
        else:
            obj.product_group = None
            obj.product_sub_group = None

    if sub_group_id is not None:
        if sub_group_id:
            try:
                obj.product_sub_group = ProductCreationSubGroup.objects.get(
                    id=sub_group_id, group=obj.product_group
                )
            except ProductCreationSubGroup.DoesNotExist:
                return Response({"status": False, "message": "Invalid sub group for selected group"}, status=400)
        else:
            obj.product_sub_group = None

    obj.save()
    return Response({"status": True, "message": "Updated successfully"})


@api_view(['PATCH'])
def toggle_product(request, pk):
    try:
        obj = ProductCreation.objects.get(id=pk)
    except ProductCreation.DoesNotExist:
        return Response({"status": False, "message": "Product not found"}, status=404)
    obj.is_active = not obj.is_active
    obj.save()
    return Response({"status": True})


# ── Dropdown helpers ──────────────────────────────────────────────────────────

@api_view(['GET'])
def company_dropdown(request):
    data = [{"id": obj.pk, "company_name": obj.name} for obj in Company.objects.all()]
    return Response({"status": True, "data": data})


@api_view(['GET'])
def group_dropdown(request):
    data = ItemGroup.objects.filter(is_active=True).values('id', 'group_name', 'code')
    return Response({"status": True, "data": list(data)})


@api_view(['GET'])
def sub_group_dropdown(request):
    group_id = request.GET.get('group_id')
    queryset = SubGroup.objects.filter(is_active=True)
    if group_id:
        queryset = queryset.filter(group_id=group_id)
    return Response({"status": True, "data": list(queryset.values('id', 'sub_group_name', 'sub_group_code'))})


# ── Product-Creation-specific group management (isolated tables) ──────────────

@api_view(['GET'])
def product_group_management(request):
    groups = ProductCreationGroup.objects.prefetch_related('sub_groups').all()
    data = [
        {
            'id': g.pk,
            'group_name': g.name,
            'sub_groups': [{'id': sg.pk, 'sub_group_name': sg.name} for sg in g.sub_groups.all()],
        }
        for g in groups
    ]
    return Response({"status": True, "data": data})


@api_view(['DELETE'])
def delete_product_group(request, pk):
    try:
        group = ProductCreationGroup.objects.get(pk=pk)
    except ProductCreationGroup.DoesNotExist:
        return Response({"status": False, "message": "Group not found"}, status=404)

    if ProductCreation.objects.filter(product_group=group).exists():
        return Response({"status": False, "message": "Cannot delete group — it is used by one or more products."}, status=400)

    group.delete()
    return Response({"status": True, "message": "Group deleted successfully"})


@api_view(['DELETE'])
def delete_product_sub_group(request, pk):
    try:
        sub_group = ProductCreationSubGroup.objects.get(pk=pk)
    except ProductCreationSubGroup.DoesNotExist:
        return Response({"status": False, "message": "Sub group not found"}, status=404)

    if ProductCreation.objects.filter(product_sub_group=sub_group).exists():
        return Response({"status": False, "message": "Cannot delete sub group — it is used by one or more products."}, status=400)

    sub_group.delete()
    return Response({"status": True, "message": "Sub group deleted successfully"})


@api_view(['GET'])
def product_group_dropdown(request):
    data = [{'id': g.pk, 'group_name': g.name} for g in ProductCreationGroup.objects.all()]
    return Response({"status": True, "data": data})


@api_view(['POST'])
def create_product_group(request):
    group_name = request.data.get('group_name', '').strip()
    if not group_name:
        return Response({"status": False, "message": "Group name is required"}, status=400)
    if ProductCreationGroup.objects.filter(name__iexact=group_name).exists():
        return Response({"status": False, "message": "Group name already exists"}, status=400)

    group = ProductCreationGroup.objects.create(name=group_name)
    return Response({
        "status": True,
        "message": "Group created successfully",
        "data": {"id": group.pk, "group_name": group.name},
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def product_sub_group_dropdown(request):
    group_id = request.GET.get('group_id')
    if not group_id:
        return Response({"status": True, "data": []})

    data = [
        {'id': sg.pk, 'sub_group_name': sg.name, 'group_id': sg.group_id}
        for sg in ProductCreationSubGroup.objects.filter(group_id=group_id)
    ]
    return Response({"status": True, "data": data})


@api_view(['POST'])
def create_product_sub_group(request):
    group_id = request.data.get('group_id')
    name = request.data.get('sub_group_name', '').strip()

    if not group_id:
        return Response({"status": False, "message": "Group is required"}, status=400)
    if not name:
        return Response({"status": False, "message": "Sub group name is required"}, status=400)

    try:
        group = ProductCreationGroup.objects.get(id=group_id)
    except ProductCreationGroup.DoesNotExist:
        return Response({"status": False, "message": "Invalid group"}, status=400)

    if ProductCreationSubGroup.objects.filter(name__iexact=name, group=group).exists():
        return Response({"status": False, "message": "Sub group already exists in this group"}, status=400)

    sub_group = ProductCreationSubGroup.objects.create(group=group, name=name)
    return Response({
        "status": True,
        "message": "Sub group created successfully",
        "data": {"id": sub_group.pk, "sub_group_name": sub_group.name, "group_id": sub_group.group_id},
    }, status=status.HTTP_201_CREATED)
# Standard BOM - This file defines the API views for managing standard bills of materials (BOM) in the production module of the MASTERS app, including path-based views for listing BOMs with pagination and search functionality, creating new BOMs with multiple items, viewing BOM details, and updating existing BOMs. The views handle HTTP requests and return appropriate responses based on the operations performed on the StandardBOM and StandardBOMItem models, allowing for organized management of BOM data within the system. Additionally, there are validations in place to ensure data integrity during BOM creation and updates.
# LIST ALL BOMS
@api_view(['GET'])
def bom_list(request):
    """Get all BOM records with product details"""
    try:
        queryset = StandardBOM.objects.select_related('product', 'semi_finished').all()
        serializer = StandardBOMSerializer(queryset, many=True)
        return Response({
            "status": True,
            "message": "BOMs fetched successfully",
            "data": serializer.data,
            "count": queryset.count()
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": False,
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# CREATE BOM WITH VALIDATION
@api_view(['POST'])
def create_bom(request):
    """Create a new BOM with multiple items
    
    Expected JSON:
    {
        "product_id": 1,
        "items": [
            {
                "item_id": 1,
                "qty": 5,
                "unit": "PCS",
                "remarks": "Optional remarks",
                "is_active": true
            }
        ]
    }
    """
    try:
        # Validate input data
        serializer = CreateBOMSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        validated_data = cast(dict[str, Any], serializer.validated_data)
        product_id = validated_data.get('product_id')
        semi_finished_id = validated_data.get('semi_finished_id')
        items = cast(list[dict[str, Any]], validated_data.get('items', []))

        product = None
        semi_finished = None
        try:
            if product_id is not None:
                product = ProductCreation.objects.get(id=product_id)
            else:
                semi_finished = ItemMaster.objects.get(id=semi_finished_id)
        except (ProductCreation.DoesNotExist, ItemMaster.DoesNotExist):
            return Response({
                "status": False,
                "message": "Selected BOM material not found"
            }, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            bom = StandardBOM.objects.create(product=product, semi_finished=semi_finished)

            for row in items:
                item = ItemMaster.objects.get(id=row.get('item_id'))
                StandardBOMItem.objects.create(
                    bom=bom,
                    item=item,
                    qty=row.get('qty'),
                    unit=row.get('unit'),
                    remarks=row.get('remarks', ''),
                    is_active=row.get('is_active', True)
                )

        # Return created BOM with details
        bom_serializer = StandardBOMSerializer(bom)
        return Response({
            "status": True,
            "message": "BOM created successfully",
            "data": bom_serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "status": False,
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# VIEW BOM DETAILS
@api_view(['GET'])
def view_bom(request, pk):
    """Get BOM details by ID"""
    try:
        bom = StandardBOM.objects.select_related('product', 'semi_finished').get(id=pk)
        serializer = StandardBOMSerializer(bom)
        return Response({
            "status": True,
            "message": "BOM details fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    except StandardBOM.DoesNotExist:
        return Response({
            "status": False,
            "message": f"BOM with ID {pk} not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "status": False,
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# UPDATE BOM ITEMS
@api_view(['PUT'])
def update_bom(request, pk):
    """Update BOM product and items"""
    try:
        bom = StandardBOM.objects.get(id=pk)
        product_id = request.data.get('product_id')
        semi_finished_id = request.data.get('semi_finished_id')
        items = cast(list[dict[str, Any]], request.data.get('items', []))

        if bool(product_id) == bool(semi_finished_id):
            return Response({
                "status": False,
                "message": "Select either product or semi-finished item"
            }, status=status.HTTP_400_BAD_REQUEST)

        product = None
        semi_finished = None
        if product_id:
            try:
                product = ProductCreation.objects.get(id=product_id)
            except (ProductCreation.DoesNotExist, TypeError, ValueError):
                return Response({
                    "status": False,
                    "message": f"Product with ID {product_id} not found"
                }, status=status.HTTP_404_NOT_FOUND)

            if StandardBOM.objects.filter(product=product).exclude(id=bom.id).exists():
                return Response({
                    "status": False,
                    "message": "This product already has a Standard BOM"
                }, status=status.HTTP_400_BAD_REQUEST)

        if semi_finished_id:
            try:
                semi_finished = ItemMaster.objects.get(id=semi_finished_id)
            except (ItemMaster.DoesNotExist, TypeError, ValueError):
                return Response({
                    "status": False,
                    "message": f"Semi-finished item with ID {semi_finished_id} not found"
                }, status=status.HTTP_404_NOT_FOUND)

            if StandardBOM.objects.filter(semi_finished=semi_finished).exclude(id=bom.id).exists():
                return Response({
                    "status": False,
                    "message": "This semi-finished item already has a Standard BOM"
                }, status=status.HTTP_400_BAD_REQUEST)

        if not items:
            return Response({
                "status": False,
                "message": "Items are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        for row in items:
            try:
                ItemMaster.objects.get(id=row.get('item_id'))
            except (ItemMaster.DoesNotExist, TypeError, ValueError):
                return Response({
                    "status": False,
                    "message": f"Item with ID {row.get('item_id')} not found"
                }, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            bom.product = product
            bom.semi_finished = semi_finished
            bom.save(update_fields=["product", "semi_finished"])
            StandardBOMItem.objects.filter(bom=bom).delete()

            for row in items:
                item = ItemMaster.objects.get(id=row.get('item_id'))
                StandardBOMItem.objects.create(
                    bom=bom,
                    item=item,
                    qty=row.get('qty'),
                    unit=row.get('unit'),
                    remarks=row.get('remarks', ''),
                    is_active=row.get('is_active', True)
                )

        bom_serializer = StandardBOMSerializer(bom)
        return Response({
            "status": True,
            "message": "BOM updated successfully",
            "data": bom_serializer.data
        }, status=status.HTTP_200_OK)

    except StandardBOM.DoesNotExist:
        return Response({
            "status": False,
            "message": f"BOM with ID {pk} not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "status": False,
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# DELETE BOM
@api_view(['DELETE'])
def delete_bom(request, pk):
    """Delete BOM by ID"""
    try:
        bom = StandardBOM.objects.select_related('product', 'semi_finished').get(id=pk)
        bom_name = bom.product.product_name if bom.product_id and bom.product else bom.semi_finished.item_name
        bom.delete()
        return Response({
            "status": True,
            "message": f"BOM '{bom_name}' deleted successfully"
        }, status=status.HTTP_200_OK)
    except StandardBOM.DoesNotExist:
        return Response({
            "status": False,
            "message": f"BOM with ID {pk} not found"
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "status": False,
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# PRODUCT DROPDOWN
@api_view(['GET'])
def product_dropdown(request):
    """Get all active products for dropdown"""
    try:
        data = ProductCreation.objects.filter(is_active=True).values('id', 'product_name')
        return Response({
            "status": True,
            "message": "Products fetched successfully",
            "data": list(data)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": False,
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ITEM DROPDOWN
@api_view(['GET'])
def item_dropdown(request):
    """Get all active items for dropdown"""
    try:
        data = ItemMaster.objects.filter(is_active=True).values('id', 'item_name', 'item_code')
        return Response({
            "status": True,
            "message": "Items fetched successfully",
            "data": list(data)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": False,
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


unit_list = extend_schema(
    parameters=DATATABLE_PARAMETERS,
    responses=OpenApiTypes.OBJECT,
)(unit_list)
create_unit = extend_schema(
    request=UnitSerializer,
    responses=OpenApiTypes.OBJECT,
)(create_unit)
update_unit = extend_schema(
    request=UnitSerializer,
    responses=OpenApiTypes.OBJECT,
)(update_unit)
toggle_unit = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_unit)

item_group_list = extend_schema(
    parameters=[SEARCH_PARAMETER],
    responses=OpenApiTypes.OBJECT,
)(item_group_list)
create_item_group = extend_schema(
    request=OpenApiTypes.OBJECT,
    responses=OpenApiTypes.OBJECT,
)(create_item_group)
update_item_group = extend_schema(
    request=OpenApiTypes.OBJECT,
    responses=OpenApiTypes.OBJECT,
)(update_item_group)
toggle_item_group = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_item_group)

sub_group_list = extend_schema(
    parameters=[
        SEARCH_PARAMETER,
        query_int_parameter("group_id", "Optional group ID to filter sub groups."),
    ],
    responses=OpenApiTypes.OBJECT,
)(sub_group_list)
create_sub_group = extend_schema(
    request=OpenApiTypes.OBJECT,
    responses=OpenApiTypes.OBJECT,
)(create_sub_group)
update_sub_group = extend_schema(
    request=OpenApiTypes.OBJECT,
    responses=OpenApiTypes.OBJECT,
)(update_sub_group)
toggle_sub_group = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_sub_group)
group_dropdown = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(group_dropdown)

category_list = extend_schema(
    parameters=[
        SEARCH_PARAMETER,
        query_int_parameter("group_id", "Optional group ID to filter categories."),
        query_int_parameter("sub_group_id", "Optional sub group ID to filter categories."),
    ],
    responses=OpenApiTypes.OBJECT,
)(category_list)
create_category = extend_schema(
    request=OpenApiTypes.OBJECT,
    responses=OpenApiTypes.OBJECT,
)(create_category)
update_category = extend_schema(
    request=OpenApiTypes.OBJECT,
    responses=OpenApiTypes.OBJECT,
)(update_category)
toggle_category = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_category)
sub_group_dropdown = extend_schema(
    parameters=[query_int_parameter("group_id", "Optional group ID to filter sub groups.")],
    responses=OpenApiTypes.OBJECT,
)(sub_group_dropdown)

item_list = extend_schema(
    parameters=[
        SEARCH_PARAMETER,
        query_int_parameter("group_id", "Optional group ID to filter items."),
        query_int_parameter("sub_group_id", "Optional sub group ID to filter items."),
        query_int_parameter("category_id", "Optional category ID to filter items."),
    ],
    responses=OpenApiTypes.OBJECT,
)(item_list)
create_item = extend_schema(
    request=OpenApiTypes.OBJECT,
    responses=OpenApiTypes.OBJECT,
)(create_item)
toggle_item = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_item)

product_list = extend_schema(
    parameters=[
        SEARCH_PARAMETER,
        query_int_parameter("group_id", "Optional group ID to filter products."),
        query_int_parameter("sub_group_id", "Optional sub group ID to filter products."),
        query_int_parameter("company_id", "Optional company ID to filter products."),
    ],
    responses=OpenApiTypes.OBJECT,
)(product_list)
create_product = extend_schema(
    request=OpenApiTypes.OBJECT,
    responses=OpenApiTypes.OBJECT,
)(create_product)
update_product = extend_schema(
    request=OpenApiTypes.OBJECT,
    responses=OpenApiTypes.OBJECT,
)(update_product)
toggle_product = extend_schema(
    request=None,
    responses=OpenApiTypes.OBJECT,
)(toggle_product)
company_dropdown = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(company_dropdown)

bom_list = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(bom_list)
create_bom = extend_schema(
    request=CreateBOMSerializer,
    responses=OpenApiTypes.OBJECT,
)(create_bom)
view_bom = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(view_bom)
update_bom = extend_schema(
    request=OpenApiTypes.OBJECT,
    responses=OpenApiTypes.OBJECT,
)(update_bom)
delete_bom = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(delete_bom)
product_dropdown = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(product_dropdown)
item_dropdown = extend_schema(
    responses=OpenApiTypes.OBJECT,
)(item_dropdown)

class ExpenseCategoryCreateAPIView(APIView):

    def post(self, request):

        serializer = ExpenseCategorySerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class ExpenseCategoryListAPIView(APIView):

    def get(self, request):

        queryset = ExpenseCategory.objects.filter(
            is_delete=0
        )

        serializer = ExpenseCategorySerializer(
            queryset,
            many=True
        )

        return Response(serializer.data)


class ExpenseCategoryDetailAPIView(APIView):

    def get(self, request, pk):

        obj = ExpenseCategory.objects.get(
            pk=pk
        )

        serializer = ExpenseCategorySerializer(obj)

        return Response(serializer.data)


class ExpenseCategoryUpdateAPIView(APIView):

    def put(self, request, pk):

        obj = ExpenseCategory.objects.get(
            pk=pk
        )

        serializer = ExpenseCategorySerializer(
            obj,
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ExpenseCategoryDeleteAPIView(APIView):
    def delete(self, request, pk):
        obj = ExpenseCategory.objects.get(
            pk=pk
        )

        obj.is_delete = 1
        obj.save()

        return Response(
            {
                "message":
                "Expense Category Deleted Successfully"
            }
        )



class ExpenseSubCategoryCreateAPIView(
    generics.CreateAPIView
):
    queryset = ExpenseSubCategory.objects.all()
    serializer_class = ExpenseSubCategorySerializer


class ExpenseSubCategoryListAPIView(
    generics.ListAPIView
):
    queryset = ExpenseSubCategory.objects.filter(
        is_delete=0
    ).order_by("-id")

    serializer_class = ExpenseSubCategorySerializer


class ExpenseSubCategoryDetailAPIView(
    generics.RetrieveAPIView
):
    queryset = ExpenseSubCategory.objects.all()
    serializer_class = ExpenseSubCategorySerializer


class ExpenseSubCategoryUpdateAPIView(
    generics.UpdateAPIView
):
    queryset = ExpenseSubCategory.objects.all()
    serializer_class = ExpenseSubCategorySerializer


class ExpenseSubCategoryDeleteAPIView(
    generics.DestroyAPIView
):
    queryset = ExpenseSubCategory.objects.all()
    serializer_class = ExpenseSubCategorySerializer

class CustomerCategoryCreateAPIView(
    generics.CreateAPIView
):
    queryset = CustomerCategory.objects.all()
    serializer_class = CustomerCategorySerializer


class CustomerCategoryListAPIView(
    generics.ListAPIView
):
    queryset = CustomerCategory.objects.filter(
        is_delete=0
    ).order_by("-customer_category_id")

    serializer_class = CustomerCategorySerializer


class CustomerCategoryDetailAPIView(
    generics.RetrieveAPIView
):
    queryset = CustomerCategory.objects.all()
    serializer_class = CustomerCategorySerializer


class CustomerCategoryUpdateAPIView(
    generics.UpdateAPIView
):
    queryset = CustomerCategory.objects.all()
    serializer_class = CustomerCategorySerializer


class CustomerCategoryDeleteAPIView(
    generics.DestroyAPIView
):
    queryset = CustomerCategory.objects.all()
    serializer_class = CustomerCategorySerializer

class PaymentCategoryCreateAPIView(
    generics.CreateAPIView
):
    queryset = PaymentCategory.objects.all()
    serializer_class = PaymentCategorySerializer


class PaymentCategoryListAPIView(
    generics.ListAPIView
):
    queryset = PaymentCategory.objects.filter(
        is_delete=0
    ).order_by("-id")

    serializer_class = PaymentCategorySerializer


class PaymentCategoryDetailAPIView(
    generics.RetrieveAPIView
):
    queryset = PaymentCategory.objects.all()
    serializer_class = PaymentCategorySerializer


class PaymentCategoryUpdateAPIView(
    generics.UpdateAPIView
):
    queryset = PaymentCategory.objects.all()
    serializer_class = PaymentCategorySerializer


class PaymentCategoryDeleteAPIView(
    generics.DestroyAPIView
):
    queryset = PaymentCategory.objects.all()
    serializer_class = PaymentCategorySerializer
