"""Sales and expense APIs.

The module mixes document CRUD endpoints with summary screens used by the
frontend approval/report flows. Imports are kept explicit here so the file is
easier to maintain and doesn't rely on wildcard side effects.
"""

from django.shortcuts import get_object_or_404

from django.db.models import F
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from PROCUREMENT.schema_utils import (
    query_date_parameter,
    query_int_parameter,
    query_str_parameter,
)
from .models import ExpenseApproval, ExpenseEntry, OrderedBOM, SalesInvoice, SalesOrder
from .serializers import (
    ExpenseApprovalActionSerializer,
    ExpenseEntrySerializer,
    OrderedBOMSerializer,
    SalesInvoiceSerializer,
    SalesOrderListRowSerializer,
    SalesOrderSerializer,
)

#>>>>>>>>>>>>>>>>>>>>>>>>>>> Sales Invoice >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
SALES_INVOICE_FILTER_PARAMETERS = [
    query_int_parameter("company", "Filter by company id."),
    query_int_parameter("customer", "Filter by customer id."),
    query_date_parameter("from_date", "Filter from invoice date."),
    query_date_parameter("to_date", "Filter to invoice date."),
]


@extend_schema(
    operation_id="api_sales_sales_invoice_list",
    parameters=SALES_INVOICE_FILTER_PARAMETERS,
    responses={200: {"type": "object"}},
    methods=["GET"],
)
@extend_schema(
    operation_id="api_sales_sales_invoice_create",
    request=SalesInvoiceSerializer,
    responses={201: SalesInvoiceSerializer},
    methods=["POST"],
)
@api_view(["GET", "POST"])
def sales_invoice_list(request):

    if request.method == "POST":
        serializer = SalesInvoiceSerializer(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            return Response(SalesInvoiceSerializer(obj).data, status=201)
        return Response(serializer.errors, status=400)

    queryset = SalesInvoice.objects.select_related('company', 'customer', 'project')

    # Filters
    if request.GET.get("company"):
        queryset = queryset.filter(company_id=request.GET["company"])

    if request.GET.get("customer"):
        queryset = queryset.filter(customer_id=request.GET["customer"])

    if request.GET.get("from_date") and request.GET.get("to_date"):
        queryset = queryset.filter(entry_date__range=[
            request.GET["from_date"], request.GET["to_date"]
        ])

    data = []
    for i, row in enumerate(queryset, 1):
        data.append({
            "id": row.pk,
            "sno": i,
            "invoice_no": row.invoice_number,
            "company": row.company.name,
            "project": row.project.name if row.project else "",
            "customer": row.customer.name,
            "invoice_date": row.entry_date,
            "due_date": row.due_date,
            "amount": row.total_amount,
            "remarks": row.remarks,
        })

    return Response({"data": data})

@extend_schema(
    operation_id="api_sales_sales_invoice_detail",
    responses=SalesInvoiceSerializer,
    methods=["GET"],
)
@extend_schema(
    operation_id="api_sales_sales_invoice_update",
    request=SalesInvoiceSerializer,
    responses=SalesInvoiceSerializer,
    methods=["PUT"],
)
@extend_schema(
    operation_id="api_sales_sales_invoice_delete",
    responses={204: None},
    methods=["DELETE"],
)
@api_view(["GET", "PUT", "DELETE"])
def sales_invoice_detail(request, pk):
    obj = get_object_or_404(SalesInvoice, pk=pk)

    if request.method == "GET":
        return Response(SalesInvoiceSerializer(obj).data)

    if request.method == "DELETE":
        obj.delete()
        return Response(status=204)

    serializer = SalesInvoiceSerializer(obj, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=400)

#>>>>>>>>>>>>>>>>>>>>>>>>>>>> Sales Order >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

SALES_ORDER_FILTER_PARAMETERS = [
    query_int_parameter("company", "Filter by company id."),
    query_int_parameter("customer", "Filter by customer id."),
    query_str_parameter("status", "Filter by status."),
    query_date_parameter("from_date", "Filter from entry date."),
    query_date_parameter("to_date", "Filter to entry date."),
]

SALES_ORDER_LIST_RESPONSE = inline_serializer(
    name="SalesOrderListResponse",
    fields={"data": SalesOrderListRowSerializer(many=True)},
)


def _sales_order_queryset(request):
    queryset = SalesOrder.objects.select_related("company", "customer").order_by(
        "-entry_date",
        "-id",
    )

    company = request.GET.get("company")
    customer = request.GET.get("customer")
    status_filter = request.GET.get("status")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if company:
        queryset = queryset.filter(company_id=company)

    if customer:
        queryset = queryset.filter(customer_id=customer)

    if status_filter:
        queryset = queryset.filter(status=status_filter)

    if from_date and to_date:
        queryset = queryset.filter(entry_date__range=[from_date, to_date])

    return queryset


@extend_schema(
    operation_id="api_sales_sales_order_list",
    parameters=SALES_ORDER_FILTER_PARAMETERS,
    responses=SALES_ORDER_LIST_RESPONSE,
    methods=["GET"],
)
@extend_schema(
    operation_id="api_sales_sales_order_create",
    request=SalesOrderSerializer,
    responses={201: SalesOrderSerializer},
    methods=["POST"],
)
@api_view(["GET", "POST"])
def sales_order_list(request):
    if request.method == "POST":
        serializer = SalesOrderSerializer(data=request.data)
        if serializer.is_valid():
            sales_order = serializer.save()
            response_serializer = SalesOrderSerializer(sales_order)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = _sales_order_queryset(request).values(
        "id",
        "entry_date",
        "so_number",
        "so_type",
        "active_status",
        "status",
        company_name=F("company__name"),
        customer_name=F("customer__name"),
    )

    result = []
    for i, row in enumerate(data, 1):
        result.append(
            {
                "id": row["id"],
                "sno": i,
                "entry_date": row["entry_date"],
                "sales_order_no": row["so_number"],
                "company_name": row["company_name"],
                "customer_name": row["customer_name"],
                "so_type": row["so_type"],
                "active_status": row["active_status"],
                "approve_status": row["status"],
            }
        )

    return Response({"data": result})


@extend_schema(
    operation_id="api_sales_sales_order_detail",
    responses=SalesOrderSerializer,
    methods=["GET"],
)
@extend_schema(
    operation_id="api_sales_sales_order_update",
    request=SalesOrderSerializer,
    responses=SalesOrderSerializer,
    methods=["PUT"],
)
@extend_schema(
    operation_id="api_sales_sales_order_partial_update",
    request=SalesOrderSerializer,
    responses=SalesOrderSerializer,
    methods=["PATCH"],
)
@extend_schema(
    operation_id="api_sales_sales_order_delete",
    responses={204: None},
    methods=["DELETE"],
)
@api_view(["GET", "PUT", "PATCH", "DELETE"])
def sales_order_detail(request, pk):
    sales_order = get_object_or_404(
        SalesOrder.objects.select_related("company", "customer"),
        pk=pk,
    )

    if request.method == "GET":
        serializer = SalesOrderSerializer(sales_order)
        return Response(serializer.data)

    if request.method == "DELETE":
        sales_order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = SalesOrderSerializer(
        sales_order,
        data=request.data,
        partial=request.method == "PATCH",
    )
    if serializer.is_valid():
        updated_sales_order = serializer.save()
        response_serializer = SalesOrderSerializer(updated_sales_order)
        return Response(response_serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Sales BOM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@extend_schema(
    operation_id="api_sales_ordered_bom_list",
    responses={200: {"type": "object"}},
    methods=["GET"],
)
@extend_schema(
    operation_id="api_sales_ordered_bom_create",
    request=OrderedBOMSerializer,
    responses={201: OrderedBOMSerializer},
    methods=["POST"],
)
@api_view(["GET", "POST"])
def ordered_bom_list(request):

    if request.method == "POST":
        serializer = OrderedBOMSerializer(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            return Response(OrderedBOMSerializer(obj).data, status=201)
        return Response(serializer.errors, status=400)

    queryset = OrderedBOM.objects.select_related('company', 'sales_order')

    if request.GET.get("company"):
        queryset = queryset.filter(company_id=request.GET["company"])

    if request.GET.get("sales_order"):
        queryset = queryset.filter(sales_order_id=request.GET["sales_order"])

    if request.GET.get("type"):
        queryset = queryset.filter(material_type=request.GET["type"])

    data = []
    for i, row in enumerate(queryset, 1):
        data.append({
            "id": row.pk,
            "sno": i,
            "sales_order": row.sales_order.so_number,
            "so_type": row.so_type,
            "bom_type": getattr(row, "get_material_type_display")(),
        })

    return Response({"data": data})

@extend_schema(
    operation_id="api_sales_ordered_bom_detail",
    responses=OrderedBOMSerializer,
    methods=["GET"],
)
@extend_schema(
    operation_id="api_sales_ordered_bom_update",
    request=OrderedBOMSerializer,
    responses=OrderedBOMSerializer,
    methods=["PUT"],
)
@extend_schema(
    operation_id="api_sales_ordered_bom_delete",
    responses={204: None},
    methods=["DELETE"],
)
@api_view(["GET", "PUT", "DELETE"])
def ordered_bom_detail(request, pk):
    obj = get_object_or_404(OrderedBOM, pk=pk)

    if request.method == "GET":
        return Response(OrderedBOMSerializer(obj).data)

    if request.method == "DELETE":
        obj.delete()
        return Response(status=204)

    serializer = OrderedBOMSerializer(obj, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=400)

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Purchase Expense >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@extend_schema(
    operation_id="api_sales_expense_entry_list",
    responses={200: {"type": "object"}},
    methods=["GET"],
)
@extend_schema(
    operation_id="api_sales_expense_entry_create",
    request=ExpenseEntrySerializer,
    responses={201: ExpenseEntrySerializer},
    methods=["POST"],
)
@api_view(["GET", "POST"])
def expense_entry_list(request):

    if request.method == "POST":
        serializer = ExpenseEntrySerializer(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            return Response(ExpenseEntrySerializer(obj).data, status=201)
        return Response(serializer.errors, status=400)

    queryset = ExpenseEntry.objects.select_related(
        'company', 'project', 'supplier'
    )

    if request.GET.get("company"):
        queryset = queryset.filter(company_id=request.GET["company"])

    if request.GET.get("project"):
        queryset = queryset.filter(project_id=request.GET["project"])

    if request.GET.get("supplier"):
        queryset = queryset.filter(supplier_id=request.GET["supplier"])

    if request.GET.get("status"):
        queryset = queryset.filter(status=request.GET["status"])

    if request.GET.get("from_date") and request.GET.get("to_date"):
        queryset = queryset.filter(expense_date__range=[
            request.GET["from_date"], request.GET["to_date"]
        ])

    data = []
    for i, row in enumerate(queryset, 1):
        data.append({
            "id": row.pk,
            "sno": i,
            "expense_no": row.expense_number,
            "company": row.company.name,
            "project": row.project.name,
            # "category": row.category.name,
            # "sub_category": row.sub_category.name,
            "payment_type": row.payment_type,
            "supplier": row.supplier.name if row.supplier else row.manual_supplier_name,
            "expense_date": row.expense_date,
            "total_amount": row.total_amount,
            "approval_status": row.status,
        })

    return Response({"data": data})

@extend_schema(
    operation_id="api_sales_expense_entry_detail",
    responses=ExpenseEntrySerializer,
    methods=["GET"],
)
@extend_schema(
    operation_id="api_sales_expense_entry_update",
    request=ExpenseEntrySerializer,
    responses=ExpenseEntrySerializer,
    methods=["PUT"],
)
@extend_schema(
    operation_id="api_sales_expense_entry_delete",
    responses={204: None},
    methods=["DELETE"],
)
@api_view(["GET", "PUT", "DELETE"])
def expense_entry_detail(request, pk):
    obj = get_object_or_404(ExpenseEntry, pk=pk)

    if request.method == "GET":
        return Response(ExpenseEntrySerializer(obj).data)

    if request.method == "DELETE":
        obj.delete()
        return Response(status=204)

    serializer = ExpenseEntrySerializer(obj, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=400)

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Purchase Expense Approval <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

@extend_schema(
    operation_id="api_sales_expense_approval_action",
    request=ExpenseApprovalActionSerializer,
    responses={200: {"type": "object"}},
)
@api_view(["POST"])
def expense_approval_action(request):
    serializer = ExpenseApprovalActionSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    validated_data = serializer.validated_data
    assert isinstance(validated_data, dict)

    expense = get_object_or_404(ExpenseEntry, pk=validated_data["expense_id"])

    current_level = ExpenseApproval.objects.filter(
        expense=expense,
        status='pending',
    ).order_by('level').first()

    if not current_level:
        return Response({"error": "No pending approval"}, status=400)

    action = validated_data["action"]

    current_level.status = 'approved' if action == 'approve' else 'rejected'
    current_level.approved_by = request.user
    current_level.remarks = validated_data.get('remarks')
    current_level.action_date = timezone.now()
    current_level.save()

    if action == 'reject':
        expense.status = 'rejected'
        expense.save()
        return Response({"message": "Expense rejected"})

    # Check next level
    next_level = ExpenseApproval.objects.filter(expense=expense, status='pending').exists()

    if not next_level:
        expense.status = 'approved'
        expense.save()
        return Response({"message": "Fully approved"})

    return Response({"message": "Approved. Next level pending"})
