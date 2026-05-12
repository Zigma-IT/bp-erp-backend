from decimal import Decimal

from django.db import connections
from django.shortcuts import get_object_or_404
from django.db.models import F, Sum
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from PROCUREMENT.schema_utils import (
    query_date_parameter,
    query_int_parameter,
    query_str_parameter,
)
from .models import SalesOrder, SalesInvoice, Customer
from .serializers import (
    PurchaseExpenseListRowSerializer,
    PurchaseExpenseSerializer,
    SalesOrderListRowSerializer,
    SalesOrderSerializer,
    SalesInvoiceListRowSerializer,
    SalesInvoiceSerializer,
)
from purchase_master.models import ItemGroup, ProductCreation as ProductMaster, SubGroup, UnitMaster
from common_master.models import Company as CompanyMaster, Project as ProjectMaster, Tax as TaxMaster, CustomerProfile as CustomerMaster
from purchase_entrys.models import Supplier
from .models import PurchaseExpense


def _masters_db_alias():
    return "masters_db" if "masters_db" in connections.databases else "default"


def _customer_name_map(customer_ids):
    if not customer_ids:
        return {}

    queryset = CustomerMaster.objects.using(_masters_db_alias()).filter(
        pk__in=customer_ids,
        is_delete=False,
    )
    return {customer.pk: customer.customer_name for customer in queryset}


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
    queryset = SalesOrder.objects.select_related("company").order_by(
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

    data = list(_sales_order_queryset(request).values(
        "id",
        "entry_date",
        "so_number",
        "so_type",
        "active_status",
        "status",
        "customer_id",
        company_name=F("company__name"),
    ))
    customer_names = _customer_name_map(
        {row["customer_id"] for row in data if row["customer_id"]}
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
                "customer_name": customer_names.get(row["customer_id"], ""),
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
        SalesOrder.objects.select_related("company"),
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


# Sales Invoice endpoints
SALES_INVOICE_FILTER_PARAMETERS = [
    query_int_parameter("company", "Filter by company id."),
    query_int_parameter("customer", "Filter by customer id."),
    query_str_parameter("status", "Filter by status."),
    query_date_parameter("from_date", "Filter from invoice date."),
    query_date_parameter("to_date", "Filter to invoice date."),
]

SALES_INVOICE_LIST_RESPONSE = inline_serializer(
    name="SalesInvoiceListResponse",
    fields={"data": SalesInvoiceListRowSerializer(many=True)},
)

PURCHASE_EXPENSE_FILTER_PARAMETERS = [
    query_int_parameter("company", "Filter by company id."),
    query_int_parameter("project", "Filter by project id."),
    query_int_parameter("category", "Filter by category id."),
    query_int_parameter("sub_category", "Filter by sub category id."),
    query_int_parameter("supplier", "Filter by supplier id."),
    query_str_parameter("status", "Filter by status."),
    query_date_parameter("from_date", "Filter from expense date."),
    query_date_parameter("to_date", "Filter to expense date."),
]

PURCHASE_EXPENSE_LIST_RESPONSE = inline_serializer(
    name="PurchaseExpenseListResponse",
    fields={"data": PurchaseExpenseListRowSerializer(many=True)},
)


def _sales_invoice_queryset(request):
    queryset = SalesInvoice.objects.select_related("company").order_by(
        "-invoice_date",
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
        queryset = queryset.filter(invoice_date__range=[from_date, to_date])

    return queryset


def _purchase_expense_queryset(request):
    queryset = PurchaseExpense.objects.select_related(
        "company",
        "project",
        "supplier",
        "category",
        "sub_category",
    ).order_by("-expense_date", "-id")

    company = request.GET.get("company")
    project = request.GET.get("project")
    category = request.GET.get("category")
    sub_category = request.GET.get("sub_category")
    supplier = request.GET.get("supplier")
    status_filter = request.GET.get("status")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if company:
        queryset = queryset.filter(company_id=company)
    if project:
        queryset = queryset.filter(project_id=project)
    if category:
        queryset = queryset.filter(category_id=category)
    if sub_category:
        queryset = queryset.filter(sub_category_id=sub_category)
    if supplier:
        queryset = queryset.filter(supplier_id=supplier)
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if from_date and to_date:
        queryset = queryset.filter(expense_date__range=[from_date, to_date])

    return queryset


@extend_schema(
    operation_id="api_sales_sales_invoice_list",
    parameters=SALES_INVOICE_FILTER_PARAMETERS,
    responses=SALES_INVOICE_LIST_RESPONSE,
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
            sales_invoice = serializer.save()
            response_serializer = SalesInvoiceSerializer(sales_invoice)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = list(_sales_invoice_queryset(request).values(
        "id",
        "invoice_date",
        "invoice_number",
        "status",
        "customer_id",
        company_name=F("company__name"),
    ))
    customer_names = _customer_name_map(
        {row["customer_id"] for row in data if row["customer_id"]}
    )

    result = []
    for i, row in enumerate(data, 1):
        # Calculate total amount for this invoice
        amount = (
            SalesInvoice.objects.get(pk=row["id"])
            .items.aggregate(total=Sum("amount"))["total"]
            or Decimal(0)
        )
        result.append(
            {
                "id": row["id"],
                "sno": i,
                "invoice_date": row["invoice_date"],
                "invoice_number": row["invoice_number"],
                "company_name": row["company_name"],
                "customer_name": customer_names.get(row["customer_id"], ""),
                "amount": str(amount),
                "approve_status": row["status"],
            }
        )

    return Response({"data": result})


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
    operation_id="api_sales_sales_invoice_partial_update",
    request=SalesInvoiceSerializer,
    responses=SalesInvoiceSerializer,
    methods=["PATCH"],
)
@extend_schema(
    operation_id="api_sales_sales_invoice_delete",
    responses={204: None},
    methods=["DELETE"],
)
@api_view(["GET", "PUT", "PATCH", "DELETE"])
def sales_invoice_detail(request, pk):
    sales_invoice = get_object_or_404(
        SalesInvoice.objects.select_related("company").prefetch_related(
            "items__product",
            "items__unit",
        ),
        pk=pk,
    )

    if request.method == "GET":
        serializer = SalesInvoiceSerializer(sales_invoice)
        return Response(serializer.data)

    if request.method == "DELETE":
        sales_invoice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = SalesInvoiceSerializer(
        sales_invoice,
        data=request.data,
        partial=request.method == "PATCH",
    )
    if serializer.is_valid():
        updated_sales_invoice = serializer.save()
        response_serializer = SalesInvoiceSerializer(updated_sales_invoice)
        return Response(response_serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id="api_sales_purchase_expense_list",
    parameters=PURCHASE_EXPENSE_FILTER_PARAMETERS,
    responses=PURCHASE_EXPENSE_LIST_RESPONSE,
    methods=["GET"],
)
@extend_schema(
    operation_id="api_sales_purchase_expense_create",
    request=PurchaseExpenseSerializer,
    responses={201: PurchaseExpenseSerializer},
    methods=["POST"],
)
@api_view(["GET", "POST"])
def purchase_expense_list(request):
    if request.method == "POST":
        serializer = PurchaseExpenseSerializer(data=request.data)
        if serializer.is_valid():
            purchase_expense = serializer.save()
            response_serializer = PurchaseExpenseSerializer(purchase_expense)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = _purchase_expense_queryset(request).values(
        "id",
        "expense_date",
        "expense_number",
        "payment_type",
        "status",
        "supplier_manual_entry",
        "manual_supplier_name",
        company_name=F("company__name"),
        project_name=F("project__name"),
        category_name=F("category__group_name"),
        sub_category_name=F("sub_category__sub_group_name"),
        supplier_name=F("supplier__name"),
    )

    result = []
    for i, row in enumerate(data, 1):
        total_amount = (
            PurchaseExpense.objects.get(pk=row["id"])
            .items.aggregate(total=Sum("amount"))["total"]
            or Decimal(0)
        )
        result.append(
            {
                "id": row["id"],
                "sno": i,
                "expense_date": row["expense_date"],
                "expense_number": row["expense_number"],
                "company_name": row["company_name"],
                "project_name": row["project_name"] or "",
                "category_name": row["category_name"] or "",
                "sub_category_name": row["sub_category_name"] or "",
                "payment_type": row["payment_type"],
                "supplier_name": row["manual_supplier_name"]
                if row["supplier_manual_entry"] and row["manual_supplier_name"]
                else (row["supplier_name"] or ""),
                "total_amount": str(total_amount),
                "approval_status": row["status"],
            }
        )

    return Response({"data": result})


@extend_schema(
    operation_id="api_sales_purchase_expense_detail",
    responses=PurchaseExpenseSerializer,
    methods=["GET"],
)
@extend_schema(
    operation_id="api_sales_purchase_expense_update",
    request=PurchaseExpenseSerializer,
    responses=PurchaseExpenseSerializer,
    methods=["PUT"],
)
@extend_schema(
    operation_id="api_sales_purchase_expense_partial_update",
    request=PurchaseExpenseSerializer,
    responses=PurchaseExpenseSerializer,
    methods=["PATCH"],
)
@extend_schema(
    operation_id="api_sales_purchase_expense_delete",
    responses={204: None},
    methods=["DELETE"],
)
@api_view(["GET", "PUT", "PATCH", "DELETE"])
def purchase_expense_detail(request, pk):
    purchase_expense = get_object_or_404(
        PurchaseExpense.objects.select_related(
            "company",
            "project",
            "supplier",
            "category",
            "sub_category",
        ).prefetch_related("items__product", "items__unit"),
        pk=pk,
    )

    if request.method == "GET":
        serializer = PurchaseExpenseSerializer(purchase_expense)
        return Response(serializer.data)

    if request.method == "DELETE":
        purchase_expense.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = PurchaseExpenseSerializer(
        purchase_expense,
        data=request.data,
        partial=request.method == "PATCH",
    )
    if serializer.is_valid():
        updated_purchase_expense = serializer.save()
        response_serializer = PurchaseExpenseSerializer(updated_purchase_expense)
        return Response(response_serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Dropdown endpoints
@api_view(["GET"])
def companies_dropdown(request):
    """Dropdown list of companies"""
    companies = CompanyMaster.objects.all().values_list("id", "name").order_by("name")
    results = [{"id": company[0], "name": company[1]} for company in companies]
    return Response({"results": results})


@api_view(["GET"])
def customers_dropdown(request):
    """Dropdown list of customers"""
    customers = (
        CustomerMaster.objects.using(_masters_db_alias())
        .filter(is_delete=False, is_active=True)
        .values_list("id", "customer_name")
        .order_by("customer_name")
    )
    results = [{"id": customer[0], "name": customer[1]} for customer in customers]
    return Response({"results": results})


@api_view(["GET"])
def projects_dropdown(request):
    company_id = request.GET.get("company")
    queryset = ProjectMaster.objects.filter(is_active=True)
    if company_id:
        queryset = queryset.filter(company_id=company_id)
    results = [
        {"id": project.id, "name": project.name}
        for project in queryset.order_by("name")
    ]
    return Response({"results": results})


@api_view(["GET"])
def suppliers_dropdown(request):
    queryset = Supplier.objects.filter(is_active=True).order_by("name")
    results = [{"id": supplier.id, "name": supplier.name} for supplier in queryset]
    return Response({"results": results})


@api_view(["GET"])
def categories_dropdown(request):
    queryset = ItemGroup.objects.filter(is_active=True).order_by("group_name")
    results = [{"id": category.id, "name": category.group_name} for category in queryset]
    return Response({"results": results})


@api_view(["GET"])
def sub_categories_dropdown(request):
    category_id = request.GET.get("category")
    queryset = SubGroup.objects.filter(is_active=True).order_by("sub_group_name")
    if category_id:
        queryset = queryset.filter(group_id=category_id)
    results = [{"id": sub_category.id, "name": sub_category.sub_group_name} for sub_category in queryset]
    return Response({"results": results})


@api_view(["GET"])
def products_dropdown(request):
    """Dropdown list of products"""
    company_id = request.GET.get("company")
    queryset = ProductMaster.objects.all()
    
    if company_id:
        queryset = queryset.filter(company_id=company_id)
    
    results = [
        {"id": p.id, "name": p.product_name, "value": 0}
        for p in queryset.order_by("product_name")
    ]
    return Response({"results": results})


@api_view(["GET"])
def units_dropdown(request):
    """Dropdown list of units"""
    units = UnitMaster.objects.all().values_list("id", "unit_name")
    results = [{"id": u[0], "name": u[1], "value": 0} for u in units]
    return Response({"results": results})


@api_view(["GET"])
def taxes_dropdown(request):
    queryset = TaxMaster.objects.filter(is_active=True).order_by("name")
    results = [
        {"id": tax.id, "name": tax.name, "value": str(tax.value)}
        for tax in queryset
    ]
    return Response({"results": results})
