"""Procurement report endpoints.

Each API returns flattened rows that match the reporting screens used by the
frontend. The rows are also stored in report snapshot tables so generated
report data can be checked from the database.
"""

import hashlib
import json
from decimal import Decimal
from collections import defaultdict

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from purchase_entrys.models import (
    GRN,
    PurchaseOrder,
    PurchaseOrderApproval,
    PurchaseRequisition,
    SRN,
)

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


def _approved_user_name(instance):
    if instance.level2_approved_by:
        return instance.level2_approved_by.get_username()
    if instance.level1_approved_by:
        return instance.level1_approved_by.get_username()
    return ""


def _approved_at(instance):
    return instance.level2_approved_at or instance.level1_approved_at


def _authorization_status(instance):
    if getattr(instance, "level2_status", "") == "approved":
        return "Approved"
    if getattr(instance, "level1_status", "") == "approved":
        return "Approved"
    if getattr(instance, "level2_status", "") == "rejected":
        return "Rejected"
    if getattr(instance, "level1_status", "") == "rejected":
        return "Rejected"
    return instance.get_status_display()


def _format_po_level_action(approval):
    if approval is None or not approval.approved_at:
        return ""
    try:
        level_label = PurchaseOrderApproval.Level(approval.level).label
    except ValueError:
        level_label = f"Level {approval.level}"
    return f"{level_label}/{approval.approved_at.date()}"


def _append_unique(values, value):
    if value and value not in values:
        values.append(value)


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
            'level1_approved_by',
            'level2_approved_by',
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

        requisitions = list(queryset)
        pr_numbers = sorted({pr.pr_number for pr in requisitions if pr.pr_number})
        linked_po_items = defaultdict(list)
        for po in PurchaseOrder.objects.filter(pr_number__in=pr_numbers):
            linked_po_items[po.pr_number].extend(po.items_data or [])

        data = []

        for pr in requisitions:
            for item in pr.items_data or []:
                qty = _as_decimal(item.get("qty"))
                po_qty = Decimal("0.00")
                for po_item in linked_po_items.get(pr.pr_number, []):
                    if _matching_item(item, po_item):
                        po_qty += _as_decimal(po_item.get("qty"))

                pending_qty = qty - po_qty
                if pending_qty < 0:
                    pending_qty = Decimal("0.00")

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
                    "qty": qty,
                    "uom": item.get("uom", ""),
                    "pending_qty": pending_qty,
                    "remarks": item.get("remarks", "") or "",
                    "prepared_by": pr.requested_by or "",
                    "prepared_date": pr.created_at,
                    "authorized_by": _approved_user_name(pr),
                    "authorized_date": _approved_at(pr),
                    "authorized_status": pr.get_status_display(),
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
            'level1_approved_by',
            'level2_approved_by',
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

        requisitions = list(queryset)
        pr_numbers = sorted({pr.pr_number for pr in requisitions if pr.pr_number})
        purchase_orders = list(
            PurchaseOrder.objects.select_related("supplier").filter(pr_number__in=pr_numbers)
        )
        po_ids = [po.id for po in purchase_orders]

        po_by_pr = defaultdict(list)
        for po in purchase_orders:
            po_by_pr[po.pr_number].append(po)

        po_approval_map = defaultdict(dict)
        for approval in PurchaseOrderApproval.objects.filter(
            purchase_order_id__in=po_ids
        ).order_by("purchase_order_id", "level"):
            po_approval_map[approval.purchase_order_id][approval.level] = approval

        grn_map = defaultdict(list)
        for grn in GRN.objects.filter(po_id__in=po_ids).order_by("id"):
            grn_map[grn.po_id].append(grn)

        srn_map = defaultdict(list)
        for srn in SRN.objects.filter(po_id__in=po_ids).order_by("id"):
            srn_map[srn.po_id].append(srn)

        data = []

        for pr in requisitions:
            doc_status = "Closed" if pr.status == 'po_raised' else (
                "Foreclosed" if pr.status == 'foreclosed' else "Authorised"
            )

            for item in pr.items_data or []:
                qty = _as_decimal(item.get("qty"))
                uom = item.get("uom", "")
                total_po_qty = Decimal("0.00")
                po_numbers = []
                po_statuses = []
                l1_actions = []
                l2_actions = []
                l3_actions = []
                vendor_names = []
                grn_srn_numbers = []
                grn_srn_dates = []

                for po in po_by_pr.get(pr.pr_number, []):
                    matched_qty = Decimal("0.00")
                    for po_item in po.items_data or []:
                        if _matching_item(item, po_item):
                            matched_qty += _as_decimal(po_item.get("qty"))

                    if matched_qty <= 0:
                        continue

                    total_po_qty += matched_qty
                    _append_unique(po_numbers, po.po_number or "")
                    _append_unique(po_statuses, po.approval_status_label or "")
                    _append_unique(vendor_names, po.supplier.name or "")

                    approvals = po_approval_map.get(po.id, {})
                    _append_unique(
                        l1_actions,
                        _format_po_level_action(
                            approvals.get(PurchaseOrderApproval.Level.LEVEL_1)
                        ),
                    )
                    _append_unique(
                        l2_actions,
                        _format_po_level_action(
                            approvals.get(PurchaseOrderApproval.Level.LEVEL_2)
                        ),
                    )
                    _append_unique(
                        l3_actions,
                        _format_po_level_action(
                            approvals.get(PurchaseOrderApproval.Level.LEVEL_3)
                        ),
                    )

                    for grn in grn_map.get(po.id, []):
                        _append_unique(grn_srn_numbers, grn.grn_number or "")
                        if grn.invoice_date:
                            _append_unique(grn_srn_dates, str(grn.invoice_date))
                    for srn in srn_map.get(po.id, []):
                        _append_unique(grn_srn_numbers, srn.srn_number or "")
                        if srn.invoice_date:
                            _append_unique(grn_srn_dates, str(srn.invoice_date))

                item_status = "Fulfilled" if total_po_qty >= qty and total_po_qty > 0 else (
                    "Partially Fulfilled" if total_po_qty > 0 else "Pending"
                )

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
                    "qty": qty,
                    "uom": uom,
                    "po_no": "\n".join(po_numbers),
                    "po_status": "\n".join(po_statuses),
                    "l1_action_by_date": "\n".join(l1_actions),
                    "l2_action_by_date": "\n".join(l2_actions),
                    "l3_action_by_date": "\n".join(l3_actions),
                    "po_qty": total_po_qty,
                    "vendor_name": "\n".join(vendor_names),
                    "grn_srn_number": "\n".join(grn_srn_numbers),
                    "grn_srn_date": "\n".join(grn_srn_dates),
                    "prepared_by": pr.requested_by or "",
                    "prepared_date": pr.created_at,
                    "authorized_by": _approved_user_name(pr),
                    "authorized_date": _approved_at(pr),
                    "authorized_status": _authorization_status(pr),
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
        ).prefetch_related("approvals")

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

        purchase_orders = list(queryset)
        po_ids = [po.id for po in purchase_orders]
        pr_numbers = sorted({po.pr_number for po in purchase_orders if po.pr_number})

        pr_map = {
            pr.pr_number: pr
            for pr in PurchaseRequisition.objects.select_related(
                "level1_approved_by",
                "level2_approved_by",
            ).filter(pr_number__in=pr_numbers)
        }

        approved_po_map = defaultdict(list)
        for approval in PurchaseOrderApproval.objects.filter(
            purchase_order_id__in=po_ids,
            status=PurchaseOrderApproval.Status.APPROVED,
        ).order_by("purchase_order_id", "-level", "-approved_at"):
            approved_po_map[approval.purchase_order_id].append(approval)

        grn_map = defaultdict(list)
        for grn in GRN.objects.filter(po_id__in=po_ids).order_by("id"):
            grn_map[grn.po_id].append(grn)

        srn_map = defaultdict(list)
        for srn in SRN.objects.filter(po_id__in=po_ids).order_by("id"):
            srn_map[srn.po_id].append(srn)

        data = []
        snapshot_rows = []

        for po in purchase_orders:
            linked_pr = pr_map.get(po.pr_number or "")
            latest_po_approval = approved_po_map.get(po.id, [None])[0]

            prepared_by = linked_pr.requested_by if linked_pr else ""
            prepared_date = po.created_at

            authorized_by = ""
            authorized_date = None
            if linked_pr and linked_pr.level2_approved_by:
                authorized_by = linked_pr.level2_approved_by.get_username()
                authorized_date = linked_pr.level2_approved_at
            elif linked_pr and linked_pr.level1_approved_by:
                authorized_by = linked_pr.level1_approved_by.get_username()
                authorized_date = linked_pr.level1_approved_at
            elif latest_po_approval is not None:
                authorized_by = f"Level {latest_po_approval.level}"
                authorized_date = latest_po_approval.approved_at

            grn_srn_pairs = [
                (grn.grn_number, grn.invoice_date)
                for grn in grn_map.get(po.id, [])
            ] + [
                (srn.srn_number, srn.invoice_date)
                for srn in srn_map.get(po.id, [])
            ]
            grn_srn_number = "\n".join(
                number for number, _ in grn_srn_pairs if number
            )
            grn_srn_date = "\n".join(
                str(doc_date) for _, doc_date in grn_srn_pairs if doc_date
            )

            row = {
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
                "ref_so_no": "",
                "linked_pr_no": po.pr_number or "",
                "quotation_no": po.quotation_no or "",
                "prepared_by": prepared_by,
                "prepared_date": prepared_date,
                "authorized_by": authorized_by,
                "authorized_date": authorized_date,
                "grn_srn_number": grn_srn_number,
                "grn_srn_date": grn_srn_date,
                "status": po.approval_status_label,
            }
            data.append(row)
            snapshot_rows.append(
                {
                    "unit": row["unit"],
                    "project_code": row["project_code"],
                    "po_no": row["po_no"],
                    "po_date": row["po_date"],
                    "po_type": row["po_type"],
                    "vendor_code": row["vendor_code"],
                    "vendor_name": row["vendor_name"],
                    "currency": row["currency"],
                    "exchange_rate": row["exchange_rate"],
                    "basic_value": row["basic_value"],
                    "discount": row["discount"],
                    "total_value": row["total_value"],
                }
            )

        _store_report_rows(POReport, request, snapshot_rows)
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
                grn_nos = []
                grn_dates = []

                for grn in grns:
                    for grn_item in grn.items_data or []:
                        if _matching_item(po_item, grn_item):
                            received += _as_decimal(grn_item.get("received_qty"))
                            _append_unique(grn_nos, grn.grn_number or "")
                            grn_date_value = getattr(grn, 'grn_date', None) or getattr(grn, 'invoice_date', None)
                            if grn_date_value:
                                _append_unique(grn_dates, str(grn_date_value))

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
                        "uom": po_item.get("uom", ""),
                        "rate": _as_decimal(po_item.get("rate")),
                        "total_value": _as_decimal(po_item.get("amount")),
                        "grn_no": ", ".join(grn_nos),
                        "grn_date": ", ".join(grn_dates),
                        "status": purchase_order.approval_status_label,
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

        grn_po_numbers = sorted({grn.po.pr_number for grn in queryset if grn.po and getattr(grn.po, 'pr_number', None)})
        pr_map = {
            pr.pr_number: pr
            for pr in PurchaseRequisition.objects.filter(pr_number__in=grn_po_numbers)
        }

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

                linked_pr = None
                if grn.po and getattr(grn.po, 'pr_number', None):
                    linked_pr = pr_map.get(grn.po.pr_number)

                prepared_by_dt = ""
                if linked_pr:
                    prepared_by_dt = f"{linked_pr.requested_by} {linked_pr.requisition_date}"
                elif grn.created_at:
                    prepared_by_dt = str(grn.created_at.date())

                checked_by = grn.level2_checked_by.get_username() if grn.level2_checked_by else ""
                authorized_by_dt = ""
                if grn.level1_approved_by and grn.level1_approved_at:
                    authorized_by_dt = f"{grn.level1_approved_by.get_username()} {grn.level1_approved_at.date()}"

                report_status = grn.level1_status.title() if getattr(grn, 'level1_status', None) else grn.status.title()

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
                    "prepared_by_dt": prepared_by_dt,
                    "checked_by": checked_by,
                    "authorized_by_dt": authorized_by_dt,
                    "status": report_status,
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

                    # 🔥 GET FIRST SRN WITH THIS ITEM
                    first_srn = None
                    for srn in srns:
                        for srn_item in srn.items_data or []:
                            if _matching_item(po_item, srn_item):
                                first_srn = srn
                                break
                        if first_srn:
                            break

                    srn_no = first_srn.srn_number if first_srn else ""
                    srn_date = str(first_srn.srn_date) if first_srn and getattr(first_srn, 'srn_date', None) else ""
                    srn_status = first_srn.get_status_display() if first_srn else ""

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
                        "uom": po_item.get("uom", ""),
                        "rate": _as_decimal(po_item.get("rate")),
                        "amount": _as_decimal(po_item.get("amount")),
                        "srn_no": srn_no,
                        "srn_date": srn_date,
                        "status": srn_status,
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

        srn_po_numbers = sorted(
            {srn.po.pr_number for srn in queryset if srn.po and getattr(srn.po, 'pr_number', None)}
        )
        pr_map = {
            pr.pr_number: pr
            for pr in PurchaseRequisition.objects.filter(pr_number__in=srn_po_numbers)
        }

        data = []

        for srn in queryset:
            po_items = srn.po.items_data if srn.po else []
            for item in srn.items_data or []:
                po_item = next(
                    (po_line for po_line in po_items if _matching_item(po_line, item)),
                    None,
                )

                po_qty = _as_decimal(po_item.get("qty")) if po_item else _as_decimal(item.get("order_qty"))
                accepted = _as_decimal(item.get("received_qty"))
                rejected = Decimal("0.00")
                pending = po_qty - accepted
                if pending < 0:
                    pending = Decimal("0.00")

                linked_pr = None
                if srn.po and getattr(srn.po, 'pr_number', None):
                    linked_pr = pr_map.get(srn.po.pr_number)

                prepared_by_dt = ""
                if linked_pr:
                    prepared_by_dt = f"{linked_pr.requested_by} {linked_pr.requisition_date}"
                elif srn.created_at:
                    prepared_by_dt = str(srn.created_at.date())

                checked_by = srn.level1_approved_by.get_username() if srn.level1_approved_by else ""
                authorized_by_dt = ""
                if srn.level2_approved_by and srn.level2_approved_at:
                    authorized_by_dt = (
                        f"{srn.level2_approved_by.get_username()} {srn.level2_approved_at.date()}"
                    )

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

                    "item_code": po_item.get("product", "") if po_item else item.get("item_code", ""),
                    "item_name": _item_name(item),
                    "po_qty": po_qty,
                    "accepted_qty": accepted,
                    "rejected_qty": rejected,
                    "pending_qty": pending,
                    "uom": item.get("uom", ""),
                    "rate": _as_decimal(item.get("rate")),
                    "total_value": _as_decimal(item.get("amount")),
                    "prepared_by_dt": prepared_by_dt,
                    "checked_by": checked_by,
                    "authorized_by_dt": authorized_by_dt,
                    "status": _authorization_status(srn),
                })

        _store_report_rows(CompleteSRNReport, request, data)
        return Response(data)
