"""Purchase expense API views."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from common_master.models import Company as CompanyMaster
from common_master.models import Project as ProjectMaster
from purchase_master.models import ExpenseCategory, ExpenseSubCategory, PaymentCategory
from purchase_master.models import ProductCreation as ProductMaster
from purchase_master.models import UnitMaster
from purchase_entrys.models import Supplier

from .models import PurchaseExpense
from .serializers import PurchaseExpenseSerializer


def _masters_db_alias():
    return "masters_db1"


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


def _apply_filters(queryset, request):
    company_id = request.GET.get("company")
    project_id = request.GET.get("project")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    status_filter = request.GET.get("status")
    category_id = request.GET.get("expense_category_id") or request.GET.get("category")
    sub_category_id = request.GET.get("expense_sub_category_id") or request.GET.get("sub_category")
    supplier_id = request.GET.get("supplier")
    search_value = request.GET.get("search[value]", "").strip()
    if not search_value:
        search_value = request.GET.get("search", "").strip()

    if company_id:
        queryset = queryset.filter(company_id=company_id)
    if project_id:
        queryset = queryset.filter(project_id=project_id)
    if from_date:
        queryset = queryset.filter(expense_date__gte=from_date)
    if to_date:
        queryset = queryset.filter(expense_date__lte=to_date)
    if status_filter and status_filter.lower() != "all":
        queryset = queryset.filter(status=status_filter)
    if category_id:
        queryset = queryset.filter(expense_category_id=category_id)
    if sub_category_id:
        queryset = queryset.filter(expense_sub_category_id=sub_category_id)
    if supplier_id:
        queryset = queryset.filter(supplier_id=supplier_id)
    if search_value:
        queryset = queryset.filter(
            Q(expense_number__icontains=search_value)
            | Q(company__name__icontains=search_value)
            | Q(project__name__icontains=search_value)
            | Q(expense_category_name__icontains=search_value)
            | Q(expense_sub_category_name__icontains=search_value)
            | Q(payment_type_name__icontains=search_value)
            | Q(remarks__icontains=search_value)
        )
    return queryset


def _serialize_rows(expenses, meta):
    rows = []
    for index, expense in enumerate(expenses, start=meta["start"] + 1):
        supplier_name = (
            expense.manual_supplier_name
            if expense.supplier_manual_entry and expense.manual_supplier_name
            else (expense.supplier.name if expense.supplier else "")
        )
        rows.append(
            {
                "id": expense.id,
                "sno": index,
                "expense_number": expense.expense_number,
                "expense_date": expense.expense_date,
                "company_name": expense.company.name,
                "project_name": expense.project.name if expense.project else "",
                "supplier_name": supplier_name,
                "expense_category_name": expense.expense_category_name or "",
                "expense_sub_category_name": expense.expense_sub_category_name or "",
                "payment_type_name": expense.payment_type_name or "",
                "from_company": expense.from_company,
                "basic_amount": str(expense.basic_amount),
                "total_gst": str(expense.total_gst),
                "round_off": str(expense.round_off),
                "total_amount": str(expense.total_amount),
                "status": expense.status,
                "level2_status": expense.level2_status,
            }
        )
    return rows


@extend_schema(responses={200: {"type": "object"}}, methods=["GET"])
@extend_schema(request=PurchaseExpenseSerializer, responses=PurchaseExpenseSerializer, methods=["POST"])
@api_view(["GET", "POST"])
def purchase_expense_list(request):
    if request.method == "POST":
        serializer = PurchaseExpenseSerializer(data=request.data)
        if serializer.is_valid():
            expense = serializer.save()
            return Response(
                PurchaseExpenseSerializer(expense).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    meta = _parse_datatable_request(request)
    queryset = PurchaseExpense.objects.select_related("company", "project", "supplier")
    total_records = queryset.count()
    queryset = _apply_filters(queryset, request)
    filtered_records = queryset.count()
    expenses = list(queryset[meta["start"] : meta["start"] + meta["length"]])
    data = _serialize_rows(expenses, meta)
    return _build_datatable_response(meta, total_records, filtered_records, data)


@extend_schema(responses=PurchaseExpenseSerializer, methods=["GET"])
@extend_schema(request=PurchaseExpenseSerializer, responses=PurchaseExpenseSerializer, methods=["PUT"])
@extend_schema(request=PurchaseExpenseSerializer, responses=PurchaseExpenseSerializer, methods=["PATCH"])
@extend_schema(responses={204: None}, methods=["DELETE"])
@api_view(["GET", "PUT", "PATCH", "DELETE"])
def purchase_expense_detail(request, pk):
    expense = get_object_or_404(
        PurchaseExpense.objects.select_related("company", "project", "supplier"),
        pk=pk,
    )

    if request.method == "GET":
        return Response(PurchaseExpenseSerializer(expense).data)

    if request.method == "DELETE":
        expense.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = PurchaseExpenseSerializer(
        expense,
        data=request.data,
        partial=request.method == "PATCH",
    )
    if serializer.is_valid():
        updated = serializer.save()
        return Response(PurchaseExpenseSerializer(updated).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Approval actions ─────────────────────────────────────────────────────────

@extend_schema(responses={200: {"type": "object"}})
@api_view(["POST"])
def approve_purchase_expense(request, pk):
    expense = get_object_or_404(PurchaseExpense, pk=pk)
    if expense.status == "approved":
        return Response({"detail": "Already approved."}, status=status.HTTP_400_BAD_REQUEST)
    expense.status = "approved"
    expense.save(update_fields=["status", "updated_at"])
    return Response(PurchaseExpenseSerializer(expense).data)


@extend_schema(responses={200: {"type": "object"}})
@api_view(["POST"])
def reject_purchase_expense(request, pk):
    expense = get_object_or_404(PurchaseExpense, pk=pk)
    if expense.status == "rejected":
        return Response({"detail": "Already rejected."}, status=status.HTTP_400_BAD_REQUEST)
    expense.status = "rejected"
    expense.save(update_fields=["status", "updated_at"])
    return Response(PurchaseExpenseSerializer(expense).data)


# ── Approval Level 2 ──────────────────────────────────────────────────────────

@extend_schema(responses={200: {"type": "object"}}, methods=["GET"])
@api_view(["GET"])
def purchase_expense_approval_level2_list(request):
    meta = _parse_datatable_request(request)
    queryset = PurchaseExpense.objects.select_related("company", "project", "supplier").filter(
        status="approved"
    )
    total_records = queryset.count()
    level2_status_filter = request.GET.get("level2_status")
    if level2_status_filter and level2_status_filter.lower() != "all":
        queryset = queryset.filter(level2_status=level2_status_filter)
    queryset = _apply_filters(queryset, request)
    filtered_records = queryset.count()
    expenses = list(queryset[meta["start"]: meta["start"] + meta["length"]])
    data = _serialize_rows(expenses, meta)
    return _build_datatable_response(meta, total_records, filtered_records, data)


@extend_schema(responses={200: {"type": "object"}})
@api_view(["POST"])
def approve_purchase_expense_level2(request, pk):
    expense = get_object_or_404(PurchaseExpense, pk=pk)
    if expense.status != "approved":
        return Response(
            {"detail": "Level 1 approval required before Level 2."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if expense.level2_status == "approved":
        return Response({"detail": "Already approved at Level 2."}, status=status.HTTP_400_BAD_REQUEST)
    expense.level2_status = "approved"
    expense.save(update_fields=["level2_status", "updated_at"])
    return Response(PurchaseExpenseSerializer(expense).data)


@extend_schema(responses={200: {"type": "object"}})
@api_view(["POST"])
def reject_purchase_expense_level2(request, pk):
    expense = get_object_or_404(PurchaseExpense, pk=pk)
    if expense.status != "approved":
        return Response(
            {"detail": "Level 1 approval required before Level 2."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if expense.level2_status == "rejected":
        return Response({"detail": "Already rejected at Level 2."}, status=status.HTTP_400_BAD_REQUEST)
    expense.level2_status = "rejected"
    expense.save(update_fields=["level2_status", "updated_at"])
    return Response(PurchaseExpenseSerializer(expense).data)


# ── Dropdown endpoints ────────────────────────────────────────────────────────

@api_view(["GET"])
def companies_dropdown(request):
    queryset = CompanyMaster.objects.filter(is_active=True).order_by("name")
    return Response({"results": [{"id": c.id, "name": c.name} for c in queryset]})


@api_view(["GET"])
def projects_dropdown(request):
    company_id = request.GET.get("company")
    queryset = ProjectMaster.objects.filter(is_active=True)
    if company_id:
        queryset = queryset.filter(company_id=company_id)
    return Response({"results": [{"id": p.id, "name": p.name} for p in queryset.order_by("name")]})


@api_view(["GET"])
def suppliers_dropdown(request):
    queryset = Supplier.objects.filter(is_active=True).order_by("name")
    return Response({"results": [{"id": s.id, "name": s.name} for s in queryset]})


@api_view(["GET"])
def expense_categories_dropdown(request):
    queryset = (
        ExpenseCategory.objects.using(_masters_db_alias())
        .filter(is_active=1, is_delete=0)
        .order_by("category_name")
    )
    return Response(
        {"results": [{"id": c.id, "name": c.category_name} for c in queryset]}
    )


@api_view(["GET"])
def expense_sub_categories_dropdown(request):
    category_id = request.GET.get("category_id") or request.GET.get("category")
    queryset = (
        ExpenseSubCategory.objects.using(_masters_db_alias())
        .filter(is_active=1, is_delete=0)
        .order_by("sub_category_name")
    )
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    return Response(
        {"results": [{"id": s.id, "name": s.sub_category_name} for s in queryset]}
    )


@api_view(["GET"])
def payment_types_dropdown(request):
    queryset = (
        PaymentCategory.objects.using(_masters_db_alias())
        .filter(is_active=1, is_delete=0)
        .order_by("payment_name")
    )
    return Response(
        {"results": [{"id": p.id, "name": p.payment_name} for p in queryset]}
    )


@api_view(["GET"])
def products_dropdown(request):
    queryset = (
        ProductMaster.objects.using(_masters_db_alias())
        .filter(is_active=True)
        .order_by("product_name")
    )
    return Response(
        {"results": [{"id": p.id, "name": p.product_name} for p in queryset]}
    )


@api_view(["GET"])
def units_dropdown(request):
    queryset = (
        UnitMaster.objects.using(_masters_db_alias())
        .filter(is_active=True)
        .order_by("unit_name")
    )
    return Response(
        {"results": [{"id": u.id, "name": u.unit_name} for u in queryset]}
    )
