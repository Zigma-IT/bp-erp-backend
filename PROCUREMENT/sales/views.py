from django.shortcuts import get_object_or_404
from django.db.models import F
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from PROCUREMENT.schema_utils import (
    query_date_parameter,
    query_int_parameter,
    query_str_parameter,
)
from .models import SalesOrder
from .serializers import SalesOrderListRowSerializer, SalesOrderSerializer


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
        SalesOrder.objects.select_related("company", "customer").prefetch_related(
            "items__product",
            "items__unit",
        ),
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
