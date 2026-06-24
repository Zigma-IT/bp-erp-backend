"""Procurement entry APIs for purchase orders, requisitions, GRN, and SRN."""

from typing import Any, cast

from django.db.models import F, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from PROCUREMENT.schema_utils import (
    DATATABLE_PARAMETERS,
    SEARCH_PARAMETER,
    query_date_parameter,
    query_int_parameter,
    query_str_parameter,
)
from .models import (
    GRN,
    PurchaseOrder,
    PurchaseOrderApproval,
    PurchaseOrderDocument,
    PurchaseRequisitionDocument,
    PurchaseRequisition,
    RateOrder,
    RateOrderDocument,
    SRN,
    Supplier,
)
from .services import MasterDataService, UserLookupService
from .serializers import (
    CompanyDropdownSerializer,
    GRNSerializer,
    ItemDropdownSerializer,
    ProductDropdownSerializer,
    ProjectDropdownSerializer,
    PurchaseOrderApprovalActionSerializer,
    PurchaseOrderSerializer,
    PurchaseOrderDocumentCreateSerializer,
    PurchaseOrderDocumentSerializer,
    PurchaseRequisitionDocumentCreateSerializer,
    PurchaseRequisitionDocumentSerializer,
    PurchaseRequisitionListRowSerializer,
    PurchaseRequisitionSerializer,
    RateOrderDocumentCreateSerializer,
    RateOrderDocumentSerializer,
    RateOrderSerializer,
    SRNSerializer,
    SupplierSerializer,
    TaxDropdownSerializer,
    UnitDropdownSerializer,
)


# Rate order
RATE_ORDER_APPROVER_USERNAME = "ram"
RATE_ORDER_APPROVER_USER_TYPE = "purchase head"


def _rate_order_user_type_name(username):
    return UserLookupService.get_user_type_name(username)


def _is_rate_order_approver(user):
    username = user.get_username().strip() if user and user.is_authenticated else ""
    return bool(
        username
        and (
            username.lower() == RATE_ORDER_APPROVER_USERNAME
            or _rate_order_user_type_name(username) == RATE_ORDER_APPROVER_USER_TYPE
        )
    )


class RateOrderViewSet(viewsets.ModelViewSet):
    queryset = RateOrder.objects.order_by('-created_at')
    serializer_class = RateOrderSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        supplier = self.request.GET.get('supplier')
        status = self.request.GET.get('status')
        approval_status = self.request.GET.get('approval_status')

        if supplier:
            qs = qs.filter(supplier_code=supplier)

        if status:
            qs = qs.filter(status=status)

        if approval_status:
            qs = qs.filter(approval_status=approval_status)

        return qs

    @action(detail=True, methods=['patch'], url_path='toggle')
    def toggle(self, request, pk=None):
        rate_order = self.get_object()
        rate_order.status = 'inactive' if rate_order.status == 'active' else 'active'
        rate_order.save(update_fields=['status'])
        serializer = self.get_serializer(rate_order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='approve')
    def approve(self, request, pk=None):
        if not _is_rate_order_approver(request.user):
            return Response(
                {"detail": "Only Purchase Head users can approve rate orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        rate_order = self.get_object()
        rate_order.approval_status = RateOrder.ApprovalStatus.APPROVED
        rate_order.approved_by = request.user
        rate_order.approved_at = timezone.now()
        rate_order.rejected_by = None
        rate_order.rejected_at = None
        rate_order.approval_remarks = request.data.get("remarks", "") or ""
        rate_order.save(
            update_fields=[
                "approval_status",
                "approved_by",
                "approved_at",
                "rejected_by",
                "rejected_at",
                "approval_remarks",
            ]
        )
        return Response(self.get_serializer(rate_order).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='reject')
    def reject(self, request, pk=None):
        if not _is_rate_order_approver(request.user):
            return Response(
                {"detail": "Only Purchase Head users can reject rate orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        rate_order = self.get_object()
        rate_order.approval_status = RateOrder.ApprovalStatus.REJECTED
        rate_order.rejected_by = request.user
        rate_order.rejected_at = timezone.now()
        rate_order.approved_by = None
        rate_order.approved_at = None
        rate_order.approval_remarks = request.data.get("remarks", "") or ""
        rate_order.save(
            update_fields=[
                "approval_status",
                "approved_by",
                "approved_at",
                "rejected_by",
                "rejected_at",
                "approval_remarks",
            ]
        )
        return Response(self.get_serializer(rate_order).data)

    @action(
        detail=True,
        methods=["get", "post"],
        parser_classes=[MultiPartParser, FormParser],
        url_path="documents",
    )
    def documents(self, request, pk=None):
        rate_order = self.get_object()

        if request.method == "GET":
            serializer = RateOrderDocumentSerializer(
                rate_order.documents.all(), many=True, context={"request": request}
            )
            return Response(serializer.data)

        serializer = RateOrderDocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save(rate_order=rate_order)
        response_serializer = RateOrderDocumentSerializer(document, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"documents/(?P<document_id>[^/.]+)")
    def delete_document(self, request, pk=None, document_id=None):
        rate_order = self.get_object()
        document = get_object_or_404(rate_order.documents.all(), pk=document_id)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
        queryset = queryset.filter(company_code=company_id)
    if project_id:
        queryset = queryset.filter(project_code=project_id)
    if from_date:
        queryset = queryset.filter(entry_date__gte=from_date)
    if to_date:
        queryset = queryset.filter(entry_date__lte=to_date)
    if search_value:
        queryset = queryset.filter(
            Q(po_number__icontains=search_value)
            | Q(company_code__icontains=search_value)
            | Q(project_code__icontains=search_value)
            | Q(supplier_name__icontains=search_value)
            | Q(supplier_code__icontains=search_value)
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
        queryset = queryset.filter(company_code=company_id)
    if project_id:
        queryset = queryset.filter(project_code=project_id)
    if requisition_type:
        queryset = queryset.filter(requisition_type=requisition_type)
    if requisition_for:
        queryset = queryset.filter(requisition_for=requisition_for)
    if requisition_date:
        queryset = queryset.filter(requisition_date=requisition_date)
    if search_value:
        queryset = queryset.filter(
            Q(pr_number__icontains=search_value)
            | Q(company_code__icontains=search_value)
            | Q(project_code__icontains=search_value)
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
                "company_code": purchase_order.company_code,
                "company_name": purchase_order.company_code,
                "project_code": purchase_order.project_code,
                "project_name": purchase_order.project_code,
                "supplier_code": purchase_order.supplier_code,
                "supplier_name": purchase_order.supplier_name or purchase_order.supplier_code,
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
    queryset = PurchaseOrder.objects.all()
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
            "company_code": purchase_order.company_code,
            "company_name": purchase_order.company_code,
            "project_code": purchase_order.project_code,
            "project_name": purchase_order.project_code,
            "supplier_code": purchase_order.supplier_code,
            "supplier_name": purchase_order.supplier_name or purchase_order.supplier_code,
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
        queryset = queryset.filter(company_code=company)

    if project:
        queryset = queryset.filter(project_code=project)

    if supplier:
        queryset = queryset.filter(supplier_code=supplier)

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
    queryset = MasterDataService.active_products()
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
    queryset = MasterDataService.active_items().order_by("item_name")
    serializer = ItemDropdownSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(responses=CompanyDropdownSerializer(many=True))
@api_view(["GET"])
def company_dropdown(request):
    queryset = MasterDataService.active_companies().order_by("name")
    serializer = CompanyDropdownSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(
    parameters=[query_int_parameter("company", "Optional company id to filter projects.")],
    responses=ProjectDropdownSerializer(many=True),
)
@api_view(["GET"])
def project_dropdown(request):
    queryset = MasterDataService.active_projects()
    company_id = request.GET.get("company")
    if company_id:
        queryset = queryset.filter(company_id=company_id)
    serializer = ProjectDropdownSerializer(queryset.order_by("name"), many=True)
    return Response(serializer.data)


@extend_schema(responses=SupplierSerializer(many=True))
@api_view(["GET"])
def supplier_dropdown(request):
    MasterDataService.sync_procurement_suppliers()
    queryset = Supplier.objects.filter(is_active=True).order_by("name")
    serializer = SupplierSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(responses=UnitDropdownSerializer(many=True))
@api_view(["GET"])
def unit_dropdown(request):
    queryset = MasterDataService.active_units().order_by("unit_name")
    serializer = UnitDropdownSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(responses=TaxDropdownSerializer(many=True))
@api_view(["GET"])
def tax_dropdown(request):
    queryset = MasterDataService.active_taxes().order_by("name")
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
    queryset = PurchaseOrder.objects.all()
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
    purchase_order = get_object_or_404(
        PurchaseOrder.objects.prefetch_related("approvals"),
        pk=pk,
    )
    serializer = PurchaseOrderSerializer(purchase_order)
    return Response(serializer.data)


@extend_schema(
    operation_id="api_purchase_entrys_purchase_order_documents",
    request=PurchaseOrderDocumentCreateSerializer,
    responses=PurchaseOrderDocumentSerializer(many=True),
)
@api_view(["GET", "POST"])
@parser_classes([MultiPartParser, FormParser])
def purchase_order_documents(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method == "GET":
        serializer = PurchaseOrderDocumentSerializer(
            purchase_order.documents.all(),
            many=True,
        )
        return Response(serializer.data)

    serializer = PurchaseOrderDocumentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    document = serializer.save(purchase_order=purchase_order)
    response_serializer = PurchaseOrderDocumentSerializer(document)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id="api_purchase_entrys_purchase_order_document_delete",
    responses={204: None},
)
@api_view(["DELETE"])
def delete_purchase_order_document(request, pk, document_id):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    document = get_object_or_404(
        PurchaseOrderDocument,
        pk=document_id,
        purchase_order=purchase_order,
    )
    document.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


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
@api_view(["GET"])
def purchase_requisition_sublist(request):
    """Return flat PR items filtered by company + project (for PO form PR picker)."""
    company_id = request.GET.get("company")
    project_id = request.GET.get("project")

    if not company_id or not project_id:
        return Response({"data": []})

    queryset = PurchaseRequisition.objects.filter(
        company_code=company_id,
        project_code=project_id,
    ).order_by("-requisition_date", "-id")

    rows = []
    for pr in queryset:
        items_data = pr.items_data if isinstance(pr.items_data, list) else []
        for item in items_data:
            rows.append({
                "pr_id": pr.id,
                "pr_number": pr.pr_number,
                "product_name": item.get("product_name", ""),
                "description": item.get("description", item.get("product_name", "")),
                "qty": str(item.get("qty", "")),
                "uom": item.get("uom", ""),
                "remarks": item.get("remarks", ""),
                "delivery_date": item.get("delivery_date", ""),
            })

    return Response({"data": rows})


@extend_schema(
    operation_id="api_purchase_entrys_purchase_requisition_list",
    parameters=PURCHASE_REQUISITION_FILTER_PARAMETERS,
    responses=PURCHASE_REQUISITION_LIST_RESPONSE,
)
@api_view(["GET"])
def purchase_requisition_approval_list(request):
    queryset = PurchaseRequisition.objects.order_by("-requisition_date", "-id")
    rows = _apply_purchase_requisition_filters(queryset, request).values(
        "id",
        "pr_number",
        "requisition_for",
        "requisition_type",
        "requisition_date",
        "requested_by",
        "status",
        company_name=F("company_code"),
        project_name=F("project_code"),
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
@api_view(["GET", "PUT", "PATCH", "DELETE"])
def purchase_requisition_detail(request, pk):
    purchase_requisition = get_object_or_404(
        PurchaseRequisition.objects.prefetch_related("documents"),
        pk=pk,
    )

    if request.method == "GET":
        serializer = PurchaseRequisitionSerializer(purchase_requisition)
        return Response(serializer.data)

    if request.method == "DELETE":
        purchase_requisition.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    partial = request.method == "PATCH"
    serializer = PurchaseRequisitionSerializer(
        purchase_requisition, data=request.data, partial=partial
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id="api_purchase_entrys_purchase_requisition_documents",
    request=PurchaseRequisitionDocumentCreateSerializer,
    responses=PurchaseRequisitionDocumentSerializer(many=True),
)
@api_view(["GET", "POST"])
@parser_classes([MultiPartParser, FormParser])
def purchase_requisition_documents(request, pk):
    purchase_requisition = get_object_or_404(PurchaseRequisition, pk=pk)

    if request.method == "GET":
        serializer = PurchaseRequisitionDocumentSerializer(
            purchase_requisition.documents.all(),
            many=True,
        )
        return Response(serializer.data)

    serializer = PurchaseRequisitionDocumentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    document = serializer.save(purchase_requisition=purchase_requisition)
    response_serializer = PurchaseRequisitionDocumentSerializer(document)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    operation_id="api_purchase_entrys_purchase_requisition_document_delete",
    responses={204: None},
)
@api_view(["DELETE"])
def delete_purchase_requisition_document(request, pk, document_id):
    purchase_requisition = get_object_or_404(PurchaseRequisition, pk=pk)
    document = get_object_or_404(
        PurchaseRequisitionDocument,
        pk=document_id,
        purchase_requisition=purchase_requisition,
    )
    document.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

# GRN
class GRNViewSet(viewsets.ModelViewSet):
    queryset = cast(Any, GRN).objects.none()
    serializer_class = GRNSerializer

    def get_queryset(self):
        qs = cast(Any, GRN).objects.all().order_by('-created_at')
        return _apply_receipt_filters(qs, self.request)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset().select_related('po')

        data = qs.values(
            'id',
            'invoice_date',
            'supplier_invoice_no',
            'grn_number',
            'status',
            company_name=F('company_code'),
            project_name=F('project_code'),
            supplier_name=F('supplier_name'),
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
        qs = self.get_queryset().select_related('po')

        data = qs.values(
            'id',
            'invoice_date',
            'supplier_invoice_no',
            'srn_number',
            company_name=F('company_code'),
            project_name=F('project_code'),
            supplier_name=F('supplier_name'),
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
