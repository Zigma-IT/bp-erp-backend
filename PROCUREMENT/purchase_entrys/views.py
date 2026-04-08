from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from PROCUREMENT.schema_utils import (
    DATATABLE_PARAMETERS,
    SEARCH_PARAMETER,
    query_date_parameter,
    query_int_parameter,
    query_str_parameter,
)
from .models import (
    CompanyMaster,
    ProductMaster,
    ProjectMaster,
    PurchaseOrder,
    PurchaseOrderApproval,
    Supplier,
    TaxMaster,
    UnitMaster,
)
from .serializers import (
    CompanyDropdownSerializer,
    ProductDropdownSerializer,
    ProjectDropdownSerializer,
    PurchaseOrderApprovalActionSerializer,
    PurchaseOrderSerializer,
    SupplierSerializer,
    TaxDropdownSerializer,
    UnitDropdownSerializer,
)


PURCHASE_ORDER_FILTER_PARAMETERS = DATATABLE_PARAMETERS + [
    query_int_parameter("company", "Filter by company id."),
    query_int_parameter("project", "Filter by project id."),
    query_date_parameter("from_date", "Filter from entry date."),
    query_date_parameter("to_date", "Filter to entry date."),
    query_str_parameter("status", "Filter by workflow or approval status."),
]


def _parse_datatable_request(request):
    return {
        "draw": int(request.GET.get("draw", 1)),
        "start": int(request.GET.get("start", 0)),
        "length": int(request.GET.get("length", 10)),
        "search": request.GET.get("search[value]", "").strip(),
    }


def _build_datatable_response(meta, total, filtered, data):
    return Response(
        {
            "draw": meta["draw"],
            "recordsTotal": total,
            "recordsFiltered": filtered,
            "data": data,
        }
    )


def _apply_purchase_order_filters(queryset, request):
    company_id = request.GET.get("company")
    project_id = request.GET.get("project")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    search_value = request.GET.get("search[value]", "").strip()

    if company_id:
        queryset = queryset.filter(company_id=company_id)
    if project_id:
        queryset = queryset.filter(project_id=project_id)
    if from_date:
        queryset = queryset.filter(entry_date__gte=from_date)
    if to_date:
        queryset = queryset.filter(entry_date__lte=to_date)
    if search_value:
        queryset = queryset.filter(
            Q(po_number__icontains=search_value)
            | Q(company__name__icontains=search_value)
            | Q(project__name__icontains=search_value)
            | Q(supplier__name__icontains=search_value)
            | Q(remarks__icontains=search_value)
        )
    return queryset


def _approval_lookup(purchase_orders):
    approval_map = {}
    approvals = (
        PurchaseOrderApproval.objects.filter(purchase_order__in=purchase_orders)
        .order_by("purchase_order_id", "level")
    )
    for approval in approvals:
        purchase_order_pk = approval.purchase_order.pk
        if purchase_order_pk is None:
            continue
        approval_map.setdefault(purchase_order_pk, {})[approval.level] = approval
    return approval_map


def _serialize_purchase_order_rows(purchase_orders, meta):
    approval_map = _approval_lookup(purchase_orders)
    rows = []
    for index, purchase_order in enumerate(purchase_orders, start=1):
        rows.append(
            {
                "id": purchase_order.id,
                "sno": meta["start"] + index,
                "po_number": purchase_order.po_number,
                "company_name": purchase_order.company.name,
                "project_name": purchase_order.project.name,
                "supplier_name": purchase_order.supplier.name,
                "entry_date": purchase_order.entry_date,
                "net_amount": float(purchase_order.total_basic_value),
                "gross_amount": float(purchase_order.gross_amount),
                "approval_status": purchase_order.approval_status_label,
                "level_1_status": approval_map.get(purchase_order.id, {})
                .get(PurchaseOrderApproval.Level.LEVEL_1)
                .status
                if approval_map.get(purchase_order.id, {}).get(
                    PurchaseOrderApproval.Level.LEVEL_1
                )
                else PurchaseOrderApproval.Status.PENDING,
            }
        )
    return rows


def _approval_level_queryset(level, request):
    queryset = PurchaseOrder.objects.select_related("company", "project", "supplier")
    queryset = _apply_purchase_order_filters(queryset, request)

    if level == PurchaseOrderApproval.Level.LEVEL_2:
        queryset = queryset.filter(
            approvals__level=PurchaseOrderApproval.Level.LEVEL_1,
            approvals__status=PurchaseOrderApproval.Status.APPROVED,
        )
    elif level == PurchaseOrderApproval.Level.LEVEL_3:
        queryset = queryset.filter(
            approvals__level=PurchaseOrderApproval.Level.LEVEL_2,
            approvals__status=PurchaseOrderApproval.Status.APPROVED,
        )

    status_filter = request.GET.get("status")
    if status_filter and status_filter.lower() != "all":
        queryset = queryset.filter(
            approvals__level=level,
            approvals__status=status_filter,
        )

    return queryset.distinct().order_by("-entry_date", "-id")


def _serialize_approval_rows(purchase_orders, meta, current_level):
    approval_map = _approval_lookup(purchase_orders)
    rows = []

    for index, purchase_order in enumerate(purchase_orders, start=1):
        approvals = approval_map.get(purchase_order.id, {})
        level_1 = approvals.get(PurchaseOrderApproval.Level.LEVEL_1)
        level_2 = approvals.get(PurchaseOrderApproval.Level.LEVEL_2)
        level_3 = approvals.get(PurchaseOrderApproval.Level.LEVEL_3)

        row = {
            "id": purchase_order.id,
            "sno": meta["start"] + index,
            "entry_date": purchase_order.entry_date,
            "po_number": purchase_order.po_number,
            "company_name": purchase_order.company.name,
            "project_name": purchase_order.project.name,
            "supplier_name": purchase_order.supplier.name,
            "net_amount": float(purchase_order.total_basic_value),
            "gross_amount": float(purchase_order.gross_amount),
            "approval_status": level_1.status if current_level == 1 and level_1 else (
                level_2.status if current_level == 2 and level_2 else (
                    level_3.status if current_level == 3 and level_3 else "pending"
                )
            ),
        }

        if current_level >= 1:
            row.update(
                {
                    "appr_net_amount": float(level_1.approved_net_amount)
                    if level_1
                    else 0.0,
                    "appr_gross_amount": float(level_1.approved_gross_amount)
                    if level_1
                    else 0.0,
                }
            )
        if current_level >= 2:
            row.update(
                {
                    "lvl2_net_amount": float(level_2.approved_net_amount)
                    if level_2
                    else 0.0,
                    "lvl2_gross_amount": float(level_2.approved_gross_amount)
                    if level_2
                    else 0.0,
                }
            )
        if current_level >= 3:
            row.update(
                {
                    "lvl3_net_amount": float(level_3.approved_net_amount)
                    if level_3
                    else 0.0,
                    "lvl3_gross_amount": float(level_3.approved_gross_amount)
                    if level_3
                    else 0.0,
                }
            )

        rows.append(row)

    return rows


@extend_schema(
    parameters=[
        query_int_parameter("company", "Optional company id to filter products."),
        SEARCH_PARAMETER,
    ],
    responses=ProductDropdownSerializer(many=True),
)
@api_view(["GET"])
def product_dropdown(request):
    queryset = ProductMaster.objects.filter(is_active=True).select_related("company")
    company_id = request.GET.get("company")
    search_value = request.GET.get("search", "").strip()

    if company_id:
        queryset = queryset.filter(company_id=company_id)
    if search_value:
        queryset = queryset.filter(product_name__icontains=search_value)

    serializer = ProductDropdownSerializer(queryset.order_by("product_name"), many=True)
    return Response(serializer.data)


@extend_schema(responses=CompanyDropdownSerializer(many=True))
@api_view(["GET"])
def company_dropdown(request):
    queryset = CompanyMaster.objects.filter(is_active=True).order_by("name")
    serializer = CompanyDropdownSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(
    parameters=[query_int_parameter("company", "Optional company id to filter projects.")],
    responses=ProjectDropdownSerializer(many=True),
)
@api_view(["GET"])
def project_dropdown(request):
    queryset = ProjectMaster.objects.filter(is_active=True).select_related("company")
    company_id = request.GET.get("company")
    if company_id:
        queryset = queryset.filter(company_id=company_id)
    serializer = ProjectDropdownSerializer(queryset.order_by("name"), many=True)
    return Response(serializer.data)


@extend_schema(responses=SupplierSerializer(many=True))
@api_view(["GET"])
def supplier_dropdown(request):
    queryset = Supplier.objects.filter(is_active=True).order_by("name")
    serializer = SupplierSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(responses=UnitDropdownSerializer(many=True))
@api_view(["GET"])
def unit_dropdown(request):
    queryset = UnitMaster.objects.filter(is_active=True).order_by("unit_name")
    serializer = UnitDropdownSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(responses=TaxDropdownSerializer(many=True))
@api_view(["GET"])
def tax_dropdown(request):
    queryset = TaxMaster.objects.filter(is_active=True).order_by("name")
    serializer = TaxDropdownSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(
    responses={
        200: {
            "type": "array",
            "items": {"type": "object"},
        }
    }
)
@api_view(["GET"])
def purchase_order_types(request):
    data = [
        {"value": "product", "label": "Product"},
        {"value": "service", "label": "Service"},
        {"value": "asset", "label": "Asset"},
    ]
    return Response(data)


@extend_schema(
    parameters=PURCHASE_ORDER_FILTER_PARAMETERS,
    responses={200: {"type": "object"}},
)
@api_view(["GET"])
def purchase_order_list(request):
    meta = _parse_datatable_request(request)
    queryset = PurchaseOrder.objects.select_related("company", "project", "supplier")
    total_records = queryset.count()
    queryset = _apply_purchase_order_filters(queryset, request)

    status_filter = request.GET.get("status")
    if status_filter and status_filter.lower() != "all":
        queryset = queryset.filter(workflow_status=status_filter)

    filtered_records = queryset.count()
    purchase_orders = list(queryset[meta["start"] : meta["start"] + meta["length"]])
    data = _serialize_purchase_order_rows(purchase_orders, meta)
    return _build_datatable_response(meta, total_records, filtered_records, data)


@extend_schema(request=PurchaseOrderSerializer, responses=PurchaseOrderSerializer)
@api_view(["POST"])
def create_purchase_order(request):
    serializer = PurchaseOrderSerializer(data=request.data)
    if serializer.is_valid():
        purchase_order = serializer.save()
        response_serializer = PurchaseOrderSerializer(purchase_order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(responses=PurchaseOrderSerializer)
@api_view(["GET"])
def purchase_order_detail(request, pk):
    queryset = PurchaseOrder.objects.select_related(
        "company",
        "project",
        "supplier",
        "freight_tax",
        "other_tax",
        "packing_tax",
    ).prefetch_related("items__product", "items__unit", "items__tax", "approvals")
    purchase_order = get_object_or_404(queryset, pk=pk)
    serializer = PurchaseOrderSerializer(purchase_order)
    return Response(serializer.data)


@extend_schema(
    parameters=PURCHASE_ORDER_FILTER_PARAMETERS,
    responses={200: {"type": "object"}},
)
@api_view(["GET"])
def purchase_order_approval_level_1_list(request):
    meta = _parse_datatable_request(request)
    queryset = _approval_level_queryset(PurchaseOrderApproval.Level.LEVEL_1, request)
    total_records = queryset.count()
    filtered_records = total_records
    purchase_orders = list(queryset[meta["start"] : meta["start"] + meta["length"]])
    data = _serialize_approval_rows(purchase_orders, meta, current_level=1)
    return _build_datatable_response(meta, total_records, filtered_records, data)


@extend_schema(
    parameters=PURCHASE_ORDER_FILTER_PARAMETERS,
    responses={200: {"type": "object"}},
)
@api_view(["GET"])
def purchase_order_approval_level_2_list(request):
    meta = _parse_datatable_request(request)
    queryset = _approval_level_queryset(PurchaseOrderApproval.Level.LEVEL_2, request)
    total_records = queryset.count()
    filtered_records = total_records
    purchase_orders = list(queryset[meta["start"] : meta["start"] + meta["length"]])
    data = _serialize_approval_rows(purchase_orders, meta, current_level=2)
    return _build_datatable_response(meta, total_records, filtered_records, data)


@extend_schema(
    parameters=PURCHASE_ORDER_FILTER_PARAMETERS,
    responses={200: {"type": "object"}},
)
@api_view(["GET"])
def purchase_order_approval_level_3_list(request):
    meta = _parse_datatable_request(request)
    queryset = _approval_level_queryset(PurchaseOrderApproval.Level.LEVEL_3, request)
    total_records = queryset.count()
    filtered_records = total_records
    purchase_orders = list(queryset[meta["start"] : meta["start"] + meta["length"]])
    data = _serialize_approval_rows(purchase_orders, meta, current_level=3)
    return _build_datatable_response(meta, total_records, filtered_records, data)


@extend_schema(
    request=PurchaseOrderApprovalActionSerializer,
    responses={200: {"type": "object"}},
)
@api_view(["PATCH"])
def update_purchase_order_approval(request, pk, level):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    approval = get_object_or_404(
        PurchaseOrderApproval.objects.select_related("purchase_order"),
        purchase_order=purchase_order,
        level=level,
    )
    serializer = PurchaseOrderApprovalActionSerializer(
        approval,
        data=request.data,
        context={"approval": approval},
    )
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": f"Purchase order updated for level {level}.",
                "approval_status": approval.status,
                "workflow_status": purchase_order.workflow_status,
            }
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
