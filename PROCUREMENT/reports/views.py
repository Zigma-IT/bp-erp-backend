"""Procurement report endpoints.

Each API returns flattened rows that match the reporting screens used by the
frontend. The rows are also stored in report snapshot tables so generated
report data can be checked from the database.
"""

import hashlib
import json
from decimal import Decimal

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from purchase_entrys.models import GRN, PurchaseOrder, PurchaseRequisition, SRN

from .models import (
    CompleteGRNReport,
    CompletePRReport,
    CompleteSRNReport,
    POReport,
    PendingGRNReport,
    PendingPRReport,
    PendingSRNReport,
)
from .serializers import (
    CompleteGRNReportSerializer,
    CompletePRReportSerializer,
    CompleteSRNReportSerializer,
    POReportSerializer,
    PendingGRNReportSerializer,
    PendingPRReportSerializer,
    PendingSRNReportSerializer,
)


def _as_decimal(value):
    if value in (None, ""):
        return Decimal("0.00")
    return Decimal(str(value))


def _item_name(item):
    return item.get("item_name") or item.get("product_name") or ""


def _matching_item(left, right):
    return _item_name(left).strip().lower() == _item_name(right).strip().lower()


def _filter_snapshot(request):
    params = {
        key: request.GET.getlist(key)
        for key in sorted(request.GET.keys())
    }
    signature_source = json.dumps(params, sort_keys=True)
    return hashlib.sha256(signature_source.encode("utf-8")).hexdigest(), params


@transaction.atomic
def _store_report_rows(model, request, rows):
    """Replace the stored snapshot for this report and exact filter set."""
    filter_signature, filter_params = _filter_snapshot(request)
    model.objects.filter(filter_signature=filter_signature).delete()
    model.objects.bulk_create(
        [
            model(
                filter_signature=filter_signature,
                filter_params=filter_params,
                **row,
            )
            for row in rows
        ]
    )


class PendingPRReportView(APIView):

    @extend_schema(
        operation_id="api_reports_pending_pr_report",
        responses=PendingPRReportSerializer(many=True),
    )
    def get(self, request):

        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        company = request.GET.get('company')
        project = request.GET.get('project')
        status = request.GET.get('status')  # optional

        queryset = PurchaseRequisition.objects.select_related(
            'company',
            'project',
        ).filter(status='approved')

        # FILTERS
        if from_date and to_date:
            queryset = queryset.filter(requisition_date__range=[from_date, to_date])

        if company:
            queryset = queryset.filter(company_id=company)

        if project:
            queryset = queryset.filter(project_id=project)

        if status:
            queryset = queryset.filter(status=status)

        data = []

        for pr in queryset:
            for item in pr.items_data or []:
                data.append({
                    "company": pr.company.name,
                    "project": pr.project.name,
                    "pr_no": pr.pr_number,
                    "date": pr.requisition_date,
                    "type": pr.requisition_type,
                    "requisition_for": pr.requisition_for,
                    "reference_so": getattr(getattr(pr, 'reference_so', None), 'so_number', None),
                    "item_code": item.get("item_code", ""),
                    "item_name": _item_name(item),
                })

        _store_report_rows(PendingPRReport, request, data)
        return Response(data)
    
# Complete PR
class CompletePRReportView(APIView):

    @extend_schema(
        operation_id="api_reports_complete_pr_report",
        responses=CompletePRReportSerializer(many=True),
    )
    def get(self, request):

        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        company = request.GET.get('company')
        project = request.GET.get('project')
        status = request.GET.get('status')

        queryset = PurchaseRequisition.objects.select_related(
            'company',
            'project',
        ).filter(status='po_raised')

        # FILTERS
        if from_date and to_date:
            queryset = queryset.filter(
                requisition_date__range=[from_date, to_date]
            )

        if company:
            queryset = queryset.filter(
                company_id=company
            )

        if project:
            queryset = queryset.filter(
                project_id=project
            )

        if status:
            queryset = queryset.filter(
                status=status
            )

        data = []

        for pr in queryset:

            # 🔥 ITEM STATUS LOGIC
            if pr.status == 'po_raised':
                item_status = "Fulfilled"
            else:
                item_status = "Partially Fulfilled"

            # 🔥 DOCUMENT STATUS LOGIC
            if pr.status == 'po_raised':
                doc_status = "Closed"
            elif pr.status == 'foreclosed':
                doc_status = "Foreclosed"
            else:
                doc_status = "Authorised"

            for item in pr.items_data or []:
                data.append({
                    "unit": pr.company.name,
                    "project_code": pr.project.name,
                    "pr_no": pr.pr_number,
                    "pr_date": pr.requisition_date,
                    "type": pr.requisition_type,
                    "requisition_for": pr.requisition_for,
                    "ref_so_no": getattr(getattr(pr, 'reference_so', None), 'so_number', None),

                    "doc_status": doc_status,
                    "item_status": item_status,

                    "item_code": item.get("item_code", ""),
                    "item_name": _item_name(item),
                })

        _store_report_rows(CompletePRReport, request, data)
        return Response(data)
    
# PO Report
class POReportView(APIView):

    @extend_schema(
        operation_id="api_reports_po_report",
        responses=POReportSerializer(many=True),
    )
    def get(self, request):

        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        company = request.GET.get('company')
        project = request.GET.get('project')
        supplier = request.GET.get('supplier')
        status = request.GET.get('status')

        queryset = PurchaseOrder.objects.select_related(
            'company',
            'project',
            'supplier'
        )

        # FILTERS
        if from_date and to_date:
            queryset = queryset.filter(entry_date__range=[from_date, to_date])

        if company:
            queryset = queryset.filter(company_id=company)

        if project:
            queryset = queryset.filter(project_id=project)

        if supplier:
            queryset = queryset.filter(supplier_id=supplier)

        if status:
            queryset = queryset.filter(workflow_status=status)

        data = []

        for po in queryset:

            data.append({
                "unit": po.company.name,
                "project_code": po.project.name,

                "po_no": po.po_number,
                "po_date": po.entry_date,

                "po_type": po.po_type,

                "vendor_code": po.supplier.gst_no or "",
                "vendor_name": po.supplier.name,

                "currency": getattr(po, 'currency', ''),
                "exchange_rate": getattr(po, 'exchange_rate', 1) or 1,

                "basic_value": po.total_basic_value,
                "discount": getattr(po, 'discount_value', 0),
                "total_value": po.gross_amount,
            })

        _store_report_rows(POReport, request, data)
        return Response(data)
    

# Pending GRN
class PendingGRNReportView(APIView):

    @extend_schema(
        operation_id="api_reports_pending_grn_report",
        responses=PendingGRNReportSerializer(many=True),
    )
    def get(self, request):

        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        company = request.GET.get('company')
        project = request.GET.get('project')
        supplier = request.GET.get('supplier')

        purchase_orders = PurchaseOrder.objects.select_related(
            'company',
            'project',
            'supplier',
        )

        if from_date and to_date:
            purchase_orders = purchase_orders.filter(entry_date__range=[from_date, to_date])

        if company:
            purchase_orders = purchase_orders.filter(company_id=company)

        if project:
            purchase_orders = purchase_orders.filter(project_id=project)

        if supplier:
            purchase_orders = purchase_orders.filter(supplier_id=supplier)

        data = []

        for purchase_order in purchase_orders:
            grns = GRN.objects.filter(po=purchase_order)

            for po_item in purchase_order.items_data or []:
                # Pending GRN is calculated from PO quantity minus received GRN quantity.
                received = Decimal("0.00")
                for grn in grns:
                    for grn_item in grn.items_data or []:
                        if _matching_item(po_item, grn_item):
                            received += _as_decimal(grn_item.get("received_qty"))

                pending = _as_decimal(po_item.get("qty")) - received

                if pending > 0:
                    data.append({
                        "company": purchase_order.company.name,
                        "project_code": purchase_order.project.name,

                        "po_no": purchase_order.po_number,
                        "po_date": getattr(purchase_order, 'po_date', purchase_order.entry_date),
                        "po_type": purchase_order.po_type,

                        "vendor_code": purchase_order.supplier.gst_no or "",
                        "vendor_name": purchase_order.supplier.name,

                        "item_code": po_item.get("product", ""),
                        "item_name": _item_name(po_item),

                        "po_qty": _as_decimal(po_item.get("qty")),
                        "received_qty": received,
                        "pending_qty": pending,
                    })

        _store_report_rows(PendingGRNReport, request, data)
        return Response(data)


# Complete GRN
class CompleteGRNReportView(APIView):

    @extend_schema(
        operation_id="api_reports_complete_grn_report",
        responses=CompleteGRNReportSerializer(many=True),
    )
    def get(self, request):

        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        company = request.GET.get('company')
        project = request.GET.get('project')
        status = request.GET.get('status')

        queryset = GRN.objects.select_related(
            'company',
            'project',
            'supplier',
            'po'
        )

        if from_date and to_date:
            queryset = queryset.filter(invoice_date__range=[from_date, to_date])

        if company:
            queryset = queryset.filter(company_id=company)

        if project:
            queryset = queryset.filter(project_id=project)

        if status:
            queryset = queryset.filter(status=status)

        data = []

        for grn in queryset:
            po_items = grn.po.items_data if grn.po else []
            for item in grn.items_data or []:

                # 🔥 GET PO QTY
                po_item = next(
                    (po_line for po_line in po_items if _matching_item(po_line, item)),
                    None,
                )

                po_qty = _as_decimal(po_item.get("qty")) if po_item else _as_decimal(item.get("order_qty"))

                accepted = _as_decimal(item.get("received_qty"))
                rejected = _as_decimal(item.get("rejected_qty"))

                pending = po_qty - accepted

                data.append({
                    "grn_no": grn.grn_number,
                    "grn_date": getattr(grn, 'grn_date', grn.invoice_date),

                    "company": grn.company.name,
                    "project": grn.project.name,

                    "vendor_name": grn.supplier.name,

                    "supplier_invoice": grn.supplier_invoice_no,
                    "invoice_date": grn.invoice_date,

                    "challan_no": grn.dc_no,
                    "eway_bill_no": grn.eway_bill_no,

                    "po_no": grn.po.po_number if grn.po else None,

                    "item_code": po_item.get("product", "") if po_item else item.get("item_code", ""),
                    "item_name": _item_name(item),

                    "po_qty": po_qty,
                    "accepted_qty": accepted,
                    "rejected_qty": rejected,
                    "pending_qty": pending,

                    "uom": item.get("uom", ""),
                    "rate": _as_decimal(item.get("rate")),

                    "total_value": _as_decimal(item.get("amount")),
                })

        _store_report_rows(CompleteGRNReport, request, data)
        return Response(data)
    
class PendingSRNReportView(APIView):

    @extend_schema(
        operation_id="api_reports_pending_srn_report",
        responses=PendingSRNReportSerializer(many=True),
    )
    def get(self, request):

        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        company = request.GET.get('company')
        project = request.GET.get('project')
        supplier = request.GET.get('supplier')

        purchase_orders = PurchaseOrder.objects.select_related(
            'company',
            'project',
            'supplier',
        )

        if from_date and to_date:
            purchase_orders = purchase_orders.filter(entry_date__range=[from_date, to_date])

        if company:
            purchase_orders = purchase_orders.filter(company_id=company)

        if project:
            purchase_orders = purchase_orders.filter(project_id=project)

        if supplier:
            purchase_orders = purchase_orders.filter(supplier_id=supplier)

        data = []

        for purchase_order in purchase_orders:
            srns = SRN.objects.filter(po=purchase_order)

            for po_item in purchase_order.items_data or []:
                # 🔥 TOTAL SRN RECEIVED
                received = Decimal("0.00")
                for srn in srns:
                    for srn_item in srn.items_data or []:
                        if _matching_item(po_item, srn_item):
                            received += _as_decimal(srn_item.get("received_qty"))

                pending = _as_decimal(po_item.get("qty")) - received

            # ONLY PENDING
                if pending > 0:

                    data.append({
                        "company": purchase_order.company.name,
                        "project_code": purchase_order.project.name,

                        "po_no": purchase_order.po_number,
                        "po_date": getattr(purchase_order, 'po_date', purchase_order.entry_date),
                        "po_type": purchase_order.po_type,

                        "vendor_code": purchase_order.supplier.gst_no or "",
                        "vendor_name": purchase_order.supplier.name,

                        "item_code": po_item.get("product", ""),
                        "item_name": _item_name(po_item),

                        "po_qty": _as_decimal(po_item.get("qty")),
                        "received_qty": received,
                        "pending_qty": pending,
                    })

        _store_report_rows(PendingSRNReport, request, data)
        return Response(data)
    
# Complete SRN
class CompleteSRNReportView(APIView):

    @extend_schema(
        operation_id="api_reports_complete_srn_report",
        responses=CompleteSRNReportSerializer(many=True),
    )
    def get(self, request):

        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        company = request.GET.get('company')
        project = request.GET.get('project')
        status = request.GET.get('status')

        queryset = SRN.objects.select_related(
            'company',
            'project',
            'supplier',
            'po'
        )

        if from_date and to_date:
            queryset = queryset.filter(invoice_date__range=[from_date, to_date])

        if company:
            queryset = queryset.filter(company_id=company)

        if project:
            queryset = queryset.filter(project_id=project)

        if status:
            queryset = queryset.filter(status=status)

        data = []

        for srn in queryset:

            data.append({
                "srn_no": srn.srn_number,
                "srn_date": getattr(srn, 'srn_date', srn.invoice_date),

                "unit": srn.company.name,
                "project": srn.project.name,

                "vendor_name": srn.supplier.name,

                "supplier_invoice": srn.supplier_invoice_no,
                "invoice_date": srn.invoice_date,

                "challan_no": srn.dc_no,
                "eway_bill_no": srn.eway_bill_no,

                "transport_details": srn.transporter,

                "po_no": srn.po.po_number if srn.po else None,
            })

        _store_report_rows(CompleteSRNReport, request, data)
        return Response(data)
