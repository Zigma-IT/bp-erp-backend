from typing import Any, cast

from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
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
    GRN,
    ProductMaster,
    ProjectMaster,
    PurchaseOrder,
    PurchaseOrderApproval,
    PurchaseRequisition,
    RateOrder,
    SRN,
    Supplier,
    TaxMaster,
    UnitMaster,
)
from purchase_master.models import ItemMaster
from .serializers import (
    CompanyDropdownSerializer,
    GRNSerializer,
    ItemDropdownSerializer,
    ProductDropdownSerializer,
    ProjectDropdownSerializer,
    PurchaseOrderApprovalActionSerializer,
    PurchaseOrderSerializer,
    PurchaseRequisitionListRowSerializer,
    PurchaseRequisitionSerializer,
    RateOrderSerializer,
    SRNSerializer,
    SupplierSerializer,
    TaxDropdownSerializer,
    UnitDropdownSerializer,
)

# Rate order
class RateOrderViewSet(viewsets.ModelViewSet):
    queryset = RateOrder.objects.select_related('supplier').prefetch_related('items').order_by('-created_at')
    serializer_class = RateOrderSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        supplier = self.request.GET.get('supplier')
        status = self.request.GET.get('status')

        if supplier:
            qs = qs.filter(supplier_id=supplier)

        if status:
            qs = qs.filter(status=status)

        return qs

    @action(detail=True, methods=['patch'], url_path='toggle')
    def toggle(self, request, pk=None):
        rate_order = self.get_object()
        rate_order.status = 'inactive' if rate_order.status == 'active' else 'active'
        rate_order.save(update_fields=['status'])
        serializer = self.get_serializer(rate_order)
        return Response(serializer.data)

# Purchase order
PURCHASE_ORDER_FILTER_PARAMETERS = DATATABLE_PARAMETERS + [
    query_int_parameter("company", "Filter by company id."),
    query_int_parameter("project", "Filter by project id."),
    query_date_parameter("from_date", "Filter from entry date."),
    query_date_parameter("to_date", "Filter to entry date."),
    query_str_parameter("status", "Filter by workflow or approval status."),
]

PURCHASE_REQUISITION_FILTER_PARAMETERS = [
    query_str_parameter("pr_number", "Filter by requisition number."),
    query_int_parameter("company", "Filter by company id."),
    query_int_parameter("project", "Filter by project id."),
    query_str_parameter("requisition_type", "Filter by requisition type."),
    query_str_parameter("requisition_for", "Filter by requisition purpose."),
    query_date_parameter("req_date", "Filter by requisition date."),
    SEARCH_PARAMETER,
]

PURCHASE_REQUISITION_LIST_RESPONSE = inline_serializer(
    name="PurchaseRequisitionListResponse",
    fields={"data": PurchaseRequisitionListRowSerializer(many=True)},
)


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


def _apply_purchase_requisition_filters(queryset, request):
    pr_number = request.GET.get("pr_number")
    company_id = request.GET.get("company")
    project_id = request.GET.get("project")
    requisition_type = request.GET.get("requisition_type")
    requisition_for = request.GET.get("requisition_for")
    requisition_date = request.GET.get("req_date") or request.GET.get(
        "requisition_date"
    )
    search_value = request.GET.get("search", "").strip()
    if not search_value:
        search_value = request.GET.get("search[value]", "").strip()

    if pr_number:
        queryset = queryset.filter(pr_number__icontains=pr_number)
    if company_id:
        queryset = queryset.filter(company_id=company_id)
    if project_id:
        queryset = queryset.filter(project_id=project_id)
    if requisition_type:
        queryset = queryset.filter(requisition_type=requisition_type)
    if requisition_for:
        queryset = queryset.filter(requisition_for=requisition_for)
    if requisition_date:
        queryset = queryset.filter(requisition_date=requisition_date)
    if search_value:
        queryset = queryset.filter(
            Q(pr_number__icontains=search_value)
            | Q(company__name__icontains=search_value)
            | Q(project__name__icontains=search_value)
            | Q(requested_by__icontains=search_value)
            | Q(requisition_type__icontains=search_value)
            | Q(requisition_for__icontains=search_value)
            | Q(status__icontains=search_value)
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


def _apply_receipt_filters(queryset, request):
    from_date = request.GET.get("from")
    to_date = request.GET.get("to")
    company = request.GET.get("company")
    project = request.GET.get("project")
    supplier = request.GET.get("supplier")
    status_value = request.GET.get("status")

    if from_date and to_date:
        queryset = queryset.filter(invoice_date__range=[from_date, to_date])

    if company:
        queryset = queryset.filter(company_id=company)

    if project:
        queryset = queryset.filter(project_id=project)

    if supplier:
        queryset = queryset.filter(supplier_id=supplier)

    if status_value:
        queryset = queryset.filter(status=status_value)

    return queryset


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


@extend_schema(responses=ItemDropdownSerializer(many=True))
@api_view(["GET"])
def item_dropdown(request):
    queryset = ItemMaster.objects.filter(is_active=True).order_by("item_name")
    serializer = ItemDropdownSerializer(queryset, many=True)
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
    operation_id="api_purchase_purchase_order_list",
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


@extend_schema(
    operation_id="api_purchase_purchase_order_detail",
    responses=PurchaseOrderSerializer,
)
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


# Purchase Requisition
@extend_schema(
    operation_id="api_purchase_entrys_purchase_requisition_list",
    parameters=PURCHASE_REQUISITION_FILTER_PARAMETERS,
    responses=PURCHASE_REQUISITION_LIST_RESPONSE,
)
@api_view(["GET"])
def purchase_requisition_approval_list(request):
    queryset = PurchaseRequisition.objects.select_related("company", "project").order_by(
        "-requisition_date",
        "-id",
    )
    rows = _apply_purchase_requisition_filters(queryset, request).values(
        "id",
        "pr_number",
        "requisition_for",
        "requisition_type",
        "requisition_date",
        "requested_by",
        "status",
        company_name=F("company__name"),
        project_name=F("project__name"),
    )

    data = []
    for index, row in enumerate(rows, start=1):
        data.append(
            {
                "id": row["id"],
                "sno": index,
                "pr_number": row["pr_number"],
                "company_name": row["company_name"],
                "project_name": row["project_name"],
                "requisition_for": row["requisition_for"],
                "requisition_type": row["requisition_type"],
                "requisition_date": row["requisition_date"],
                "requested_by": row["requested_by"],
                "status": row["status"],
            }
        )

    return Response({"data": data})


@extend_schema(
    operation_id="api_purchase_entrys_purchase_requisition_create",
    request=PurchaseRequisitionSerializer,
    responses=PurchaseRequisitionSerializer,
)
@api_view(["POST"])
def create_purchase_requisition(request):
    serializer = PurchaseRequisitionSerializer(data=request.data)
    if serializer.is_valid():
        purchase_requisition = serializer.save()
        response_serializer = PurchaseRequisitionSerializer(purchase_requisition)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id="api_purchase_entrys_purchase_requisition_detail",
    responses=PurchaseRequisitionSerializer,
)
@api_view(["GET"])
def purchase_requisition_detail(request, pk):
    purchase_requisition = get_object_or_404(
        PurchaseRequisition.objects.select_related("company", "project").prefetch_related(
            "items"
        ),
        pk=pk,
    )
    serializer = PurchaseRequisitionSerializer(purchase_requisition)
    return Response(serializer.data)

# GRN
class GRNViewSet(viewsets.ModelViewSet):
    queryset = cast(Any, GRN).objects.none()
    serializer_class = GRNSerializer

    def get_queryset(self):
        qs = cast(Any, GRN).objects.all().order_by('-created_at')
        return _apply_receipt_filters(qs, self.request)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().select_related('company', 'project', 'supplier', 'po')

        data = qs.values(
            'id',
            'invoice_date',
            'supplier_invoice_no',
            'grn_number',
            'status',
            company_name=F('company__name'),
            project_name=F('project__name'),
            supplier_name=F('supplier__name'),
            po_number=F('po__po_number'),
        )

        result = []
        for i, row in enumerate(data, 1):
            result.append({
                "id": row["id"],
                "sno": i,
                "company_name": row['company_name'],
                "project_name": row['project_name'],
                "supplier_name": row['supplier_name'],
                "invoice_date": row['invoice_date'],
                "po_number": row['po_number'],
                "grn_number": row['grn_number'],
                "supplier_invoice_no": row['supplier_invoice_no'],
                "approve_status": row['status'],
            })

        return Response({"data": result})

# SRN
class SRNViewSet(viewsets.ModelViewSet):
    queryset = cast(Any, SRN).objects.none()
    serializer_class = SRNSerializer

    def get_queryset(self):
        qs = cast(Any, SRN).objects.all().order_by('-created_at')
        return _apply_receipt_filters(qs, self.request)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().select_related('company', 'project', 'supplier', 'po')

        data = qs.values(
            'id',
            'invoice_date',
            'supplier_invoice_no',
            'srn_number',
            company_name=F('company__name'),
            project_name=F('project__name'),
            supplier_name=F('supplier__name'),
            po_number=F('po__po_number'),
        )

        result = []
        for i, row in enumerate(data, 1):
            result.append({
                "id": row["id"],
                "sno": i,
                "company_name": row['company_name'],
                "project_name": row['project_name'],
                "supplier_name": row['supplier_name'],
                "invoice_date": row['invoice_date'],
                "po_number": row['po_number'],
                "srn_number": row['srn_number'],
                "supplier_invoice_no": row['supplier_invoice_no'],
                "approve_status": "pending",
            })

        return Response({"data": result})
