"""Approval workflows for procurement documents.

This module groups the approval APIs that sit on top of purchase-entry and
sales records. The goal is to keep the approval rules easy to trace for both
backend and frontend developers:

- PR/GRN/SRN approvals are exposed as small DRF viewsets with approve/reject
  actions.
- Purchase-order approvals are function-based because the UI needs custom
  summary rows and a dedicated action payload.
- Sales-order approvals are read-only summary/detail endpoints.
"""

from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from PROCUREMENT.schema_utils import (
    SEARCH_PARAMETER,
    query_date_parameter,
    query_int_parameter,
    query_str_parameter,
)
from purchase_entrys.models import GRN, PurchaseRequisition, SRN
from sales.models import SalesOrder, SalesInvoice

from .models import PurchaseOrder, PurchaseOrderApproval
from .serializers import (
    GRNApprovalLevel1Serializer,
    GRNApprovalLevel2Serializer,
    PRApprovalLevel1Serializer,
    PRApprovalLevel2Serializer,
    SalesOrderApprovalDetailSerializer,
    SalesOrderApprovalListRowSerializer,
    SalesInvoiceApprovalDetailSerializer,
    SalesInvoiceApprovalListRowSerializer,
    SalesInvoiceCreateUpdateSerializer,
    SRNApprovalLevel1Serializer,
    SRNApprovalLevel2Serializer,
)


# Purchase Rquisition Approval Level 1
APPROVAL_REMARKS_REQUEST = inline_serializer(
    name="ApprovalRemarksRequest",
    fields={
        "remarks": serializers.CharField(required=False, allow_blank=True),
    },
)

APPROVAL_ACTION_RESPONSE = inline_serializer(
    name="ApprovalActionResponse",
    fields={
        "message": serializers.CharField(),
    },
)

PO_APPROVAL_FILTER_PARAMETERS = [
    query_int_parameter("company", "Filter by company id."),
    query_int_parameter("project", "Filter by project id."),
    query_date_parameter("from_date", "Filter from entry date."),
    query_date_parameter("to_date", "Filter to entry date."),
    query_str_parameter("status", "Filter by approval status."),
    SEARCH_PARAMETER,
]

PO_APPROVAL_LIST_ROW_SERIALIZER = inline_serializer(
    name="POApprovalListRow",
    fields={
        "sno": serializers.IntegerField(),
        "id": serializers.IntegerField(),
        "entry_date": serializers.DateField(),
        "po_number": serializers.CharField(),
        "company_name": serializers.CharField(),
        "project_name": serializers.CharField(),
        "supplier_name": serializers.CharField(),
        "net_amount": serializers.DecimalField(max_digits=12, decimal_places=2),
        "gross_amount": serializers.DecimalField(max_digits=12, decimal_places=2),
        "approve_status": serializers.CharField(),
    },
)

PO_APPROVAL_LIST_RESPONSE = inline_serializer(
    name="POApprovalListResponse",
    fields={"data": PO_APPROVAL_LIST_ROW_SERIALIZER},
)

RECEIPT_APPROVAL_FILTER_PARAMETERS = [
    query_int_parameter("company", "Filter by company id."),
    query_int_parameter("project", "Filter by project id."),
    query_int_parameter("supplier", "Filter by supplier id."),
    query_str_parameter("status", "Filter by approval status."),
    query_date_parameter("from", "Filter from invoice date."),
    query_date_parameter("to", "Filter to invoice date."),
]


def _request_user_or_none(request):
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return user
    return None


def _approval_remarks(request):
    return request.data.get("remarks") or request.data.get("approval_notes") or ""


@extend_schema_view(
    list=extend_schema(
        parameters=[query_str_parameter("status", "Filter by level 1 approval status.")],
        responses=PRApprovalLevel1Serializer(many=True),
    ),
    approve=extend_schema(
        request=APPROVAL_REMARKS_REQUEST,
        responses=APPROVAL_ACTION_RESPONSE,
    ),
    reject=extend_schema(
        request=APPROVAL_REMARKS_REQUEST,
        responses=APPROVAL_ACTION_RESPONSE,
    ),
)
class PRApprovalLevel1ViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequisition.objects.all()
    serializer_class = PRApprovalLevel1Serializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Only show Level 1 relevant records
        status_param = self.request.query_params.get('status')

        if status_param:
            queryset = queryset.filter(level1_status=status_param)

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        pr = self.get_object()

        # Level 1 approval moves the document forward to the next approver.
        pr.level1_status = 'approved'
        pr.level1_approved_by = request.user
        pr.level1_approved_at = timezone.now()
        pr.status = 'pending'
        pr.save()

        return Response({'message': 'Level 1 Approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        pr = self.get_object()

        pr.level1_status = 'rejected'
        pr.level1_remarks = request.data.get('remarks')
        pr.level1_approved_by = request.user
        pr.level1_approved_at = timezone.now()
        pr.status = 'rejected'
        pr.save()

        return Response({'message': 'Level 1 Rejected'})
    

# Purchase Requisition Approval Level2
@extend_schema_view(
    list=extend_schema(
        parameters=[
            query_str_parameter(
                "status",
                "Alias for level2_status. Useful for consistent frontend filters.",
            ),
            query_str_parameter("level2_status", "Filter by level 2 approval status."),
        ],
        responses=PRApprovalLevel2Serializer(many=True),
    ),
    approve=extend_schema(
        request=APPROVAL_REMARKS_REQUEST,
        responses=APPROVAL_ACTION_RESPONSE,
    ),
    reject=extend_schema(
        request=APPROVAL_REMARKS_REQUEST,
        responses=APPROVAL_ACTION_RESPONSE,
    ),
)
class PRApprovalLevel2ViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequisition.objects.all()
    serializer_class = PRApprovalLevel2Serializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(level1_status='approved')

        # Accept both keys so the frontend can use a consistent `status` filter
        # across approval screens without breaking the older query name.
        status_param = (
            self.request.query_params.get('level2_status')
            or self.request.query_params.get('status')
        )
        if status_param:
            queryset = queryset.filter(level2_status=status_param)

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        pr = self.get_object()

        # paste here
        # Level 2 is only valid after the first approver has finished.
        if pr.level1_status != 'approved':
            return Response(
                {'error': 'Level 1 approval pending'},
                status=status.HTTP_400_BAD_REQUEST
            )

        pr.level2_status = 'approved'
        pr.level2_approved_by = request.user
        pr.level2_approved_at = timezone.now()
        pr.status = 'approved'
        pr.save()

        return Response({'message': 'Level 2 Approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        pr = self.get_object()

        # paste here also
        # Rejections at level 2 must respect the same approval order.
        if pr.level1_status != 'approved':
            return Response(
                {'error': 'Level 1 approval pending'},
                status=status.HTTP_400_BAD_REQUEST
            )

        pr.level2_status = 'rejected'
        pr.level2_remarks = request.data.get('remarks')
        pr.level2_approved_by = request.user
        pr.level2_approved_at = timezone.now()
        pr.status = 'rejected'
        pr.save()

        return Response({'message': 'Level 2 Rejected'})

# >>>>>>>>>>>>>>>>>>>>>>>>>> Purchase order approvals levels >>>>>>>>>>>>>>>>>>>>>>>>>>>>>

PO_APPROVAL_ACTION_REQUEST = inline_serializer(
    name="POApprovalActionRequest",
    fields={
        "level": serializers.IntegerField(),
        "action": serializers.ChoiceField(
            choices=["approve", "reject"],
            required=False,
        ),
        "status": serializers.ChoiceField(
            choices=PurchaseOrderApproval.Status.choices,
            required=False,
        ),
        "approved_net_amount": serializers.DecimalField(
            max_digits=12,
            decimal_places=2,
            required=False,
        ),
        "approved_gross_amount": serializers.DecimalField(
            max_digits=12,
            decimal_places=2,
            required=False,
        ),
        "remarks": serializers.CharField(required=False, allow_blank=True),
    },
)

def _po_base_queryset(request):
    # The approval screens work from a single PO summary queryset so every
    # level sees the same filtered document set before level-specific rules run.
    queryset = PurchaseOrder.objects.select_related(
        "company",
        "project",
        "supplier",
    ).prefetch_related("approvals").order_by("-entry_date", "-id")

    company = request.GET.get("company")
    project = request.GET.get("project")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    search = request.GET.get("search", "").strip()
    if not search:
        search = request.GET.get("search[value]", "").strip()

    if company:
        queryset = queryset.filter(company_id=company)

    if project:
        queryset = queryset.filter(project_id=project)

    if from_date:
        queryset = queryset.filter(entry_date__gte=from_date)

    if to_date:
        queryset = queryset.filter(entry_date__lte=to_date)

    if search:
        queryset = queryset.filter(
            Q(po_number__icontains=search)
            | Q(company__name__icontains=search)
            | Q(project__name__icontains=search)
            | Q(supplier__name__icontains=search)
        )

    return queryset


def _approval_lookup(purchase_order):
    return {approval.level: approval for approval in purchase_order.approvals.all()}


def _filter_purchase_orders_for_level(request, level):
    # Only surface purchase orders that are eligible for the requested level.
    # Higher levels are hidden until the previous level is approved.
    status_filter = request.GET.get("status", "").strip().lower()
    purchase_orders = []

    for purchase_order in _po_base_queryset(request):
        approvals = _approval_lookup(purchase_order)
        current_approval = approvals.get(level)
        if current_approval is None:
            continue

        if level > PurchaseOrderApproval.Level.LEVEL_1:
            previous_approval = approvals.get(level - 1)
            if (
                previous_approval is None
                or previous_approval.status != PurchaseOrderApproval.Status.APPROVED
            ):
                continue

        if status_filter and status_filter != "all":
            if current_approval.status != status_filter:
                continue
        elif current_approval.status != PurchaseOrderApproval.Status.PENDING:
            continue

        purchase_orders.append(purchase_order)

    return purchase_orders


def _serialize_po_rows(purchase_orders, level):
    rows = []

    for index, purchase_order in enumerate(purchase_orders, start=1):
        approvals = _approval_lookup(purchase_order)
        current_approval = approvals.get(level)
        current_status = (
            current_approval.status
            if current_approval
            else PurchaseOrderApproval.Status.PENDING
        )
        rows.append(
            {
                "sno": index,
                "id": purchase_order.pk,
                "entry_date": purchase_order.entry_date,
                "po_number": purchase_order.po_number,
                "company_name": purchase_order.company.name,
                "project_name": purchase_order.project.name,
                "supplier_name": purchase_order.supplier.name,
                "net_amount": purchase_order.total_basic_value,
                "gross_amount": purchase_order.gross_amount,
                "approve_status": f"Level {level} {current_status.title()}",
            }
        )

    return rows

@extend_schema(
    operation_id="api_approvals_po_approval_level_1_list",
    parameters=PO_APPROVAL_FILTER_PARAMETERS,
    responses=PO_APPROVAL_LIST_RESPONSE,
)
@api_view(["GET"])
def po_approval_level_1_list(request):
    purchase_orders = _filter_purchase_orders_for_level(
        request,
        PurchaseOrderApproval.Level.LEVEL_1,
    )
    return Response({"data": _serialize_po_rows(purchase_orders, level=1)})

@extend_schema(
    operation_id="api_approvals_po_approval_level_2_list",
    parameters=PO_APPROVAL_FILTER_PARAMETERS,
    responses=PO_APPROVAL_LIST_RESPONSE,
)
@api_view(["GET"])
def po_approval_level_2_list(request):
    purchase_orders = _filter_purchase_orders_for_level(
        request,
        PurchaseOrderApproval.Level.LEVEL_2,
    )
    return Response({"data": _serialize_po_rows(purchase_orders, level=2)})

@extend_schema(
    operation_id="api_approvals_po_approval_level_3_list",
    parameters=PO_APPROVAL_FILTER_PARAMETERS,
    responses=PO_APPROVAL_LIST_RESPONSE,
)
@api_view(["GET"])
def po_approval_level_3_list(request):
    purchase_orders = _filter_purchase_orders_for_level(
        request,
        PurchaseOrderApproval.Level.LEVEL_3,
    )
    return Response({"data": _serialize_po_rows(purchase_orders, level=3)})

@extend_schema(
    operation_id="api_approvals_po_approval_action_post",
    request=PO_APPROVAL_ACTION_REQUEST,
    responses={200: {"type": "object"}},
    methods=["POST"],
)
@extend_schema(
    operation_id="api_approvals_po_approval_action_patch",
    request=PO_APPROVAL_ACTION_REQUEST,
    responses={200: {"type": "object"}},
    methods=["PATCH"],
)
@api_view(["POST", "PATCH"])
def po_approval_action(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)

    try:
        level = int(request.data.get("level"))
    except (TypeError, ValueError):
        return Response(
            {"error": "A valid approval level is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    approval = get_object_or_404(
        PurchaseOrderApproval.objects.select_related("purchase_order"),
        purchase_order=purchase_order,
        level=level,
    )

    payload = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
    if not payload.get("status"):
        action_value = str(payload.get("action", "")).strip().lower()
        if action_value == "approve":
            payload["status"] = PurchaseOrderApproval.Status.APPROVED
        elif action_value == "reject":
            payload["status"] = PurchaseOrderApproval.Status.REJECTED

    if not payload.get("status"):
        return Response(
            {"error": "Provide either status or action (approve/reject)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = PurchaseOrderApprovalActionSerializer(
        approval,
        data=payload,
        context={"approval": approval},
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    return Response(
        {
            "message": "Approval updated successfully",
            "approval_status": approval.status,
            "workflow_status": approval.purchase_order.workflow_status,
        }
    )


# GRN Approval Level 1
@extend_schema_view(
    list=extend_schema(
        parameters=[query_str_parameter("status", "Filter by level 1 approval status.")],
        responses=GRNApprovalLevel1Serializer(many=True),
    ),
    approve=extend_schema(
        request=APPROVAL_REMARKS_REQUEST,
        responses=APPROVAL_ACTION_RESPONSE,
    ),
    reject=extend_schema(
        request=APPROVAL_REMARKS_REQUEST,
        responses=APPROVAL_ACTION_RESPONSE,
    ),
)
class GRNApprovalLevel1ViewSet(viewsets.ModelViewSet):
    queryset = GRN.objects.all()
    serializer_class = GRNApprovalLevel1Serializer

    def get_queryset(self):
        queryset = super().get_queryset()

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(level1_status=status_param)

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        grn = self.get_object()

        grn.level1_status = 'approved'
        grn.level1_approved_by = _request_user_or_none(request)
        grn.level1_approved_at = timezone.now()
        grn.level1_remarks = _approval_remarks(request)
        grn.status = 'pending'
        grn.save()

        return Response({'message': 'GRN Level 1 Approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        grn = self.get_object()

        grn.level1_status = 'rejected'
        grn.level1_remarks = _approval_remarks(request)
        grn.level1_approved_by = _request_user_or_none(request)
        grn.level1_approved_at = timezone.now()
        grn.status = 'rejected'
        grn.save()

        return Response({'message': 'GRN Level 1 Rejected'})
    
# GRN Approval Level 2
@extend_schema_view(
    list=extend_schema(
        parameters=[query_str_parameter("status", "Filter by level 2 approval status.")],
        responses=GRNApprovalLevel2Serializer(many=True),
    ),
    approve=extend_schema(
        request=APPROVAL_REMARKS_REQUEST,
        responses=APPROVAL_ACTION_RESPONSE,
    ),
    reject=extend_schema(
        request=APPROVAL_REMARKS_REQUEST,
        responses=APPROVAL_ACTION_RESPONSE,
    ),
)
class GRNApprovalLevel2ViewSet(viewsets.ModelViewSet):
    queryset = GRN.objects.all()
    serializer_class = GRNApprovalLevel2Serializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # ONLY Level 1 approved GRNs
        queryset = queryset.filter(level1_status='approved')

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(level2_status=status_param)

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        grn = self.get_object()

        # 🔴 critical validation
        if grn.level1_status != 'approved':
            return Response({'error': 'Level 1 approval pending'}, status=400)

        grn.level2_status = 'approved'
        grn.level2_checked_by = _request_user_or_none(request)
        grn.level2_checked_at = timezone.now()
        grn.level2_remarks = _approval_remarks(request)
        grn.status = 'checked'
        grn.save()

        return Response({'message': 'GRN Level 2 Approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        grn = self.get_object()

        if grn.level1_status != 'approved':
            return Response({'error': 'Level 1 approval pending'}, status=400)

        grn.level2_status = 'rejected'
        grn.level2_remarks = _approval_remarks(request)
        grn.level2_checked_by = _request_user_or_none(request)
        grn.level2_checked_at = timezone.now()
        grn.status = 'rejected'
        grn.save()

        return Response({'message': 'GRN Level 2 Rejected'})
    

# SRN Approval Level 1
@extend_schema_view(
    list=extend_schema(
        parameters=RECEIPT_APPROVAL_FILTER_PARAMETERS,
        responses=SRNApprovalLevel1Serializer(many=True),
    ),
    approve=extend_schema(
        request=APPROVAL_REMARKS_REQUEST,
        responses=APPROVAL_ACTION_RESPONSE,
    ),
    reject=extend_schema(
        request=APPROVAL_REMARKS_REQUEST,
        responses=APPROVAL_ACTION_RESPONSE,
    ),
)
class SRNApprovalLevel1ViewSet(viewsets.ModelViewSet):
    queryset = SRN.objects.all()
    serializer_class = SRNApprovalLevel1Serializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # filters from UI
        company = self.request.query_params.get('company')
        project = self.request.query_params.get('project')
        supplier = self.request.query_params.get('supplier')
        status = self.request.query_params.get('status')
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')

        if company:
            queryset = queryset.filter(company_id=company)

        if project:
            queryset = queryset.filter(project_id=project)

        if supplier:
            queryset = queryset.filter(supplier_id=supplier)

        if status:
            queryset = queryset.filter(level1_status=status)

        if from_date and to_date:
            queryset = queryset.filter(invoice_date__range=[from_date, to_date])

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        srn = self.get_object()

        srn.level1_status = 'approved'
        srn.level1_approved_by = request.user
        srn.level1_approved_at = timezone.now()
        srn.status = 'pending'
        srn.save()

        return Response({'message': 'SRN Approved (Level 1)'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        srn = self.get_object()

        srn.level1_status = 'rejected'
        srn.level1_remarks = request.data.get('remarks')
        srn.level1_approved_by = request.user
        srn.level1_approved_at = timezone.now()
        srn.status = 'rejected'
        srn.save()

        return Response({'message': 'SRN Rejected (Level 1)'})
    


# SRN Approval Level 2
@extend_schema_view(
    list=extend_schema(
        parameters=RECEIPT_APPROVAL_FILTER_PARAMETERS,
        responses=SRNApprovalLevel2Serializer(many=True),
    ),
    approve=extend_schema(
        request=APPROVAL_REMARKS_REQUEST,
        responses=APPROVAL_ACTION_RESPONSE,
    ),
    reject=extend_schema(
        request=APPROVAL_REMARKS_REQUEST,
        responses=APPROVAL_ACTION_RESPONSE,
    ),
)
class SRNApprovalLevel2ViewSet(viewsets.ModelViewSet):
    queryset = SRN.objects.all()    
    serializer_class = SRNApprovalLevel2Serializer

    def get_queryset(self):
        queryset = super().get_queryset()

        company = self.request.query_params.get('company')
        project = self.request.query_params.get('project')
        supplier = self.request.query_params.get('supplier')
        status = self.request.query_params.get('status')
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')

        if company:
            queryset = queryset.filter(company_id=company)

        if project:
            queryset = queryset.filter(project_id=project)

        if supplier:
            queryset = queryset.filter(supplier_id=supplier)

        if status:
            queryset = queryset.filter(level2_status=status)

        if from_date and to_date:
            queryset = queryset.filter(invoice_date__range=[from_date, to_date])

        # 🔥 IMPORTANT: Only Level 1 approved items should appear here
        queryset = queryset.filter(level1_status='approved')

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        srn = self.get_object()

        if srn.level1_status != 'approved':
            return Response({'error': 'Level 1 not approved'}, status=400)

        srn.level2_status = 'approved'
        srn.level2_approved_by = request.user
        srn.level2_approved_at = timezone.now()
        srn.status = 'checked'
        srn.save()

        return Response({'message': 'SRN Approved (Level 2)'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        srn = self.get_object()

        srn.level2_status = 'rejected'
        srn.level2_remarks = request.data.get('remarks')
        srn.level2_approved_by = request.user
        srn.level2_approved_at = timezone.now()
        srn.status = 'rejected'
        srn.save()

        return Response({'message': 'SRN Rejected (Level 2)'})

# Sales order approval

APPROVAL_FILTER_PARAMETERS = [
    query_int_parameter("company", "Filter by company id."),
    query_int_parameter("customer", "Filter by customer id."),
    query_str_parameter("active_status", "Filter by active status."),
    query_str_parameter("status", "Filter by approval status."),
    query_date_parameter("from_date", "Filter from entry date."),
    query_date_parameter("to_date", "Filter to entry date."),
    SEARCH_PARAMETER,
]

SALES_ORDER_APPROVAL_LIST_RESPONSE = inline_serializer(
    name="SalesOrderApprovalListResponse",
    fields={"data": SalesOrderApprovalListRowSerializer(many=True)},
)


def _approval_queryset(request):
    queryset = SalesOrder.objects.select_related("company", "customer").order_by(
        "-entry_date",
        "-id",
    )

    company_id = request.GET.get("company")
    customer_id = request.GET.get("customer")
    active_status = request.GET.get("active_status")
    status_filter = request.GET.get("status")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    search_value = request.GET.get("search", "").strip()
    if not search_value:
        search_value = request.GET.get("search[value]", "").strip()

    if company_id:
        queryset = queryset.filter(company_id=company_id)
    if customer_id:
        queryset = queryset.filter(customer_id=customer_id)
    if active_status:
        queryset = queryset.filter(active_status=active_status)
    if status_filter and status_filter.lower() != "all":
        queryset = queryset.filter(status=status_filter)
    if from_date:
        queryset = queryset.filter(entry_date__gte=from_date)
    if to_date:
        queryset = queryset.filter(entry_date__lte=to_date)
    if search_value:
        queryset = queryset.filter(
            Q(so_number__icontains=search_value)
            | Q(company__name__icontains=search_value)
            | Q(customer__customer_name__icontains=search_value)
            | Q(so_type__icontains=search_value)
            | Q(active_status__icontains=search_value)
            | Q(status__icontains=search_value)
        )

    return queryset


@extend_schema(
    operation_id="api_approvals_sales_order_approval_list",
    parameters=APPROVAL_FILTER_PARAMETERS,
    responses=SALES_ORDER_APPROVAL_LIST_RESPONSE,
)
@api_view(["GET"])
def sales_order_approval_list(request):
    queryset = _approval_queryset(request)
    rows = queryset.values(
        "id",
        "entry_date",
        "so_number",
        "so_type",
        "active_status",
        "status",
        company_name=F("company__name"),
        customer_name=F("customer__customer_name"),
    )

    data = []
    for index, row in enumerate(rows, start=1):
        data.append(
            {
                "id": row["id"],
                "sno": index,
                "entry_date": row["entry_date"],
                "sales_order_no": row["so_number"],
                "company_name": row["company_name"],
                "customer_name": row["customer_name"],
                "so_type": row["so_type"],
                "active_status": row["active_status"],
                "approve_status": row["status"],
            }
        )

    return Response({"data": data})


@extend_schema(
    operation_id="api_approvals_sales_order_approval_detail",
    responses=SalesOrderApprovalDetailSerializer,
)
@api_view(["GET"])
def sales_order_approval_detail(request, pk):
    sales_order = get_object_or_404(
        SalesOrder.objects.select_related("company", "customer"),
        pk=pk,
    )
    serializer = SalesOrderApprovalDetailSerializer(sales_order)
    return Response(serializer.data)


# Sales Invoice approval
SALES_INVOICE_APPROVAL_FILTER_PARAMETERS = [
    query_int_parameter("company", "Filter by company id."),
    query_int_parameter("customer", "Filter by customer id."),
    query_str_parameter("status", "Filter by approval status."),
    query_date_parameter("from_date", "Filter from invoice date."),
    query_date_parameter("to_date", "Filter to invoice date."),
    SEARCH_PARAMETER,
]

SALES_INVOICE_APPROVAL_LIST_RESPONSE = inline_serializer(
    name="SalesInvoiceApprovalListResponse",
    fields={"data": SalesInvoiceApprovalListRowSerializer(many=True)},
)


def _sales_invoice_approval_queryset(request):
    from django.db.models import Sum, DecimalField
    from django.db.models.functions import Cast

    queryset = SalesInvoice.objects.select_related("company", "customer").order_by(
        "-invoice_date",
        "-id",
    )

    company_id = request.GET.get("company")
    customer_id = request.GET.get("customer")
    status_filter = request.GET.get("status")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    search_value = request.GET.get("search", "").strip()
    if not search_value:
        search_value = request.GET.get("search[value]", "").strip()

    if company_id:
        queryset = queryset.filter(company_id=company_id)
    if customer_id:
        queryset = queryset.filter(customer_id=customer_id)
    if status_filter and status_filter.lower() != "all":
        queryset = queryset.filter(status=status_filter)
    if from_date:
        queryset = queryset.filter(invoice_date__gte=from_date)
    if to_date:
        queryset = queryset.filter(invoice_date__lte=to_date)
    if search_value:
        queryset = queryset.filter(
            Q(invoice_number__icontains=search_value)
            | Q(company__name__icontains=search_value)
            | Q(customer__customer_name__icontains=search_value)
            | Q(status__icontains=search_value)
        )

    return queryset


@extend_schema(
    operation_id="api_approvals_sales_invoice_approval_list",
    parameters=SALES_INVOICE_APPROVAL_FILTER_PARAMETERS,
    responses=SALES_INVOICE_APPROVAL_LIST_RESPONSE,
)
@api_view(["GET"])
def sales_invoice_approval_list(request):
    queryset = _sales_invoice_approval_queryset(request)
    
    # Calculate total amount for each invoice
    data = []
    for index, invoice in enumerate(queryset, start=1):
        total_amount = sum(float(item.amount or 0) for item in invoice.items.all())
        data.append(
            {
                "id": invoice.id,
                "sno": index,
                "invoice_date": invoice.invoice_date,
                "invoice_number": invoice.invoice_number,
                "company_name": invoice.company.name,
                "customer_name": invoice.customer.customer_name,
                "amount": str(total_amount),
                "approve_status": invoice.status,
            }
        )

    return Response({"data": data})


@extend_schema(
    operation_id="api_approvals_sales_invoice_approval_detail",
    responses=SalesInvoiceApprovalDetailSerializer,
)
@api_view(["GET"])
def sales_invoice_approval_detail(request, pk):
    sales_invoice = get_object_or_404(
        SalesInvoice.objects.select_related("company", "customer").prefetch_related(
            "items__product",
            "items__unit",
        ),
        pk=pk,
    )
    serializer = SalesInvoiceApprovalDetailSerializer(sales_invoice)
    return Response(serializer.data)


@extend_schema(
    operation_id="api_approvals_sales_invoice_create",
    request=SalesInvoiceCreateUpdateSerializer,
    responses=SalesInvoiceApprovalDetailSerializer,
)
@api_view(["POST"])
def sales_invoice_create(request):
    serializer = SalesInvoiceCreateUpdateSerializer(data=request.data)
    if serializer.is_valid():
        instance = serializer.save()
        # Return the detailed representation
        detail_serializer = SalesInvoiceApprovalDetailSerializer(
            SalesInvoice.objects.select_related("company", "customer").prefetch_related(
                "items__product",
                "items__unit",
            ).get(pk=instance.pk)
        )
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id="api_approvals_sales_invoice_update",
    request=SalesInvoiceCreateUpdateSerializer,
    responses=SalesInvoiceApprovalDetailSerializer,
)
@api_view(["PUT"])
def sales_invoice_update(request, pk):
    sales_invoice = get_object_or_404(SalesInvoice, pk=pk)
    serializer = SalesInvoiceCreateUpdateSerializer(sales_invoice, data=request.data)
    if serializer.is_valid():
        instance = serializer.save()
        # Return the detailed representation
        detail_serializer = SalesInvoiceApprovalDetailSerializer(
            SalesInvoice.objects.select_related("company", "customer").prefetch_related(
                "items__product",
                "items__unit",
            ).get(pk=instance.pk)
        )
        return Response(detail_serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Purchase Rquisition Approval Level 1
class PRApprovalLevel1ViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequisition.objects.select_related("company", "project").all()
    serializer_class = PRApprovalLevel1Serializer

    def get_queryset(self):
        queryset = super().get_queryset()
        pr_number = self.request.query_params.get("pr_number")
        company = self.request.query_params.get("company")
        project = self.request.query_params.get("project")
        requisition_type = self.request.query_params.get("requisition_type")
        requisition_for = self.request.query_params.get("requisition_for")
        req_date = self.request.query_params.get("req_date") or self.request.query_params.get("requisition_date")
        status_param = self.request.query_params.get("status")
        search_value = self.request.query_params.get("search", "").strip()
        if not search_value:
            search_value = self.request.query_params.get("search[value]", "").strip()

        if pr_number:
            queryset = queryset.filter(pr_number__icontains=pr_number)
        if company:
            queryset = queryset.filter(company_id=company)
        if project:
            queryset = queryset.filter(project_id=project)
        if requisition_type:
            queryset = queryset.filter(requisition_type=requisition_type)
        if requisition_for:
            queryset = queryset.filter(requisition_for=requisition_for)
        if req_date:
            queryset = queryset.filter(requisition_date=req_date)
        if status_param and status_param.lower() != "all":
            queryset = queryset.filter(status=status_param)
        if search_value:
            queryset = queryset.filter(
                Q(pr_number__icontains=search_value)
                | Q(company__name__icontains=search_value)
                | Q(project__name__icontains=search_value)
                | Q(requisition_for__icontains=search_value)
                | Q(requisition_type__icontains=search_value)
                | Q(requested_by__icontains=search_value)
                | Q(status__icontains=search_value)
            )

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        pr = self.get_object()

        pr.status = 'approved'
        pr.save(update_fields=['status'])

        return Response({'message': 'Level 1 Approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        pr = self.get_object()

        pr.status = 'rejected'
        pr.save(update_fields=['status'])

        return Response({'message': 'Level 1 Rejected'})
    

# Purchase Requisition Approval Level2
class PRApprovalLevel2ViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequisition.objects.all()
    serializer_class = PRApprovalLevel2Serializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(level1_status='approved')

        status_param = self.request.query_params.get('level2_status')
        if status_param:
            queryset = queryset.filter(level2_status=status_param)

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        pr = self.get_object()

        # paste here
        if pr.level1_status != 'approved':
            return Response(
                {'error': 'Level 1 approval pending'},
                status=status.HTTP_400_BAD_REQUEST
            )

        pr.level2_status = 'approved'
        pr.level2_approved_by = request.user
        pr.level2_approved_at = timezone.now()
        pr.status = 'approved'
        pr.save()

        return Response({'message': 'Level 2 Approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        pr = self.get_object()

        # paste here also
        if pr.level1_status != 'approved':
            return Response(
                {'error': 'Level 1 approval pending'},
                status=status.HTTP_400_BAD_REQUEST
            )

        pr.level2_status = 'rejected'
        pr.level2_remarks = request.data.get('remarks')
        pr.level2_approved_by = request.user
        pr.level2_approved_at = timezone.now()
        pr.status = 'rejected'
        pr.save()

        return Response({'message': 'Level 2 Rejected'})
    
# GRN Approval Level 1
class GRNApprovalLevel1ViewSet(viewsets.ModelViewSet):
    queryset = GRN.objects.all()
    serializer_class = GRNApprovalLevel1Serializer

    def get_queryset(self):
        queryset = super().get_queryset()

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(level1_status=status_param)

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        grn = self.get_object()

        grn.level1_status = 'approved'
        grn.level1_approved_by = _request_user_or_none(request)
        grn.level1_approved_at = timezone.now()
        grn.level1_remarks = _approval_remarks(request)
        grn.status = 'pending'
        grn.save()

        return Response({'message': 'GRN Level 1 Approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        grn = self.get_object()

        grn.level1_status = 'rejected'
        grn.level1_remarks = _approval_remarks(request)
        grn.level1_approved_by = _request_user_or_none(request)
        grn.level1_approved_at = timezone.now()
        grn.status = 'rejected'
        grn.save()

        return Response({'message': 'GRN Level 1 Rejected'})
    
# GRN Approval Level 2
class GRNApprovalLevel2ViewSet(viewsets.ModelViewSet):
    queryset = GRN.objects.all()
    serializer_class = GRNApprovalLevel2Serializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # ONLY Level 1 approved GRNs
        queryset = queryset.filter(level1_status='approved')

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(level2_status=status_param)

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        grn = self.get_object()

        # 🔴 critical validation
        if grn.level1_status != 'approved':
            return Response({'error': 'Level 1 approval pending'}, status=400)

        grn.level2_status = 'approved'
        grn.level2_checked_by = _request_user_or_none(request)
        grn.level2_checked_at = timezone.now()
        grn.level2_remarks = _approval_remarks(request)
        grn.status = 'checked'
        grn.save()

        return Response({'message': 'GRN Level 2 Approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        grn = self.get_object()

        if grn.level1_status != 'approved':
            return Response({'error': 'Level 1 approval pending'}, status=400)

        grn.level2_status = 'rejected'
        grn.level2_remarks = _approval_remarks(request)
        grn.level2_checked_by = _request_user_or_none(request)
        grn.level2_checked_at = timezone.now()
        grn.status = 'rejected'
        grn.save()

        return Response({'message': 'GRN Level 2 Rejected'})
    

# SRN Approval Level 1
class SRNApprovalLevel1ViewSet(viewsets.ModelViewSet):
    queryset = SRN.objects.all()
    serializer_class = SRNApprovalLevel1Serializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # filters from UI
        company = self.request.query_params.get('company')
        project = self.request.query_params.get('project')
        supplier = self.request.query_params.get('supplier')
        status = self.request.query_params.get('status')
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')

        if company:
            queryset = queryset.filter(company_id=company)

        if project:
            queryset = queryset.filter(project_id=project)

        if supplier:
            queryset = queryset.filter(supplier_id=supplier)

        if status:
            queryset = queryset.filter(level1_status=status)

        if from_date and to_date:
            queryset = queryset.filter(invoice_date__range=[from_date, to_date])

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        srn = self.get_object()

        srn.level1_status = 'approved'
        srn.level1_approved_by = request.user
        srn.level1_approved_at = timezone.now()
        srn.save()

        return Response({'message': 'SRN Approved (Level 1)'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        srn = self.get_object()

        srn.level1_status = 'rejected'
        srn.level1_remarks = request.data.get('remarks')
        srn.level1_approved_by = request.user
        srn.level1_approved_at = timezone.now()
        srn.save()

        return Response({'message': 'SRN Rejected (Level 1)'})
    


# SRN Approval Level 2
class SRNApprovalLevel2ViewSet(viewsets.ModelViewSet):
    queryset = SRN.objects.all()    
    serializer_class = SRNApprovalLevel2Serializer

    def get_queryset(self):
        queryset = super().get_queryset()

        company = self.request.query_params.get('company')
        project = self.request.query_params.get('project')
        supplier = self.request.query_params.get('supplier')
        status = self.request.query_params.get('status')
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')

        if company:
            queryset = queryset.filter(company_id=company)

        if project:
            queryset = queryset.filter(project_id=project)

        if supplier:
            queryset = queryset.filter(supplier_id=supplier)

        if status:
            queryset = queryset.filter(level2_status=status)

        if from_date and to_date:
            queryset = queryset.filter(invoice_date__range=[from_date, to_date])

        # 🔥 IMPORTANT: Only Level 1 approved items should appear here
        queryset = queryset.filter(level1_status='approved')

        return queryset.order_by('-id')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        srn = self.get_object()

        if srn.level1_status != 'approved':
            return Response({'error': 'Level 1 not approved'}, status=400)

        srn.level2_status = 'approved'
        srn.level2_approved_by = request.user
        srn.level2_approved_at = timezone.now()
        srn.save()

        return Response({'message': 'SRN Approved (Level 2)'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        srn = self.get_object()

        srn.level2_status = 'rejected'
        srn.level2_remarks = request.data.get('remarks')
        srn.level2_approved_by = request.user
        srn.level2_approved_at = timezone.now()
        srn.save()

        return Response({'message': 'SRN Rejected (Level 2)'})
