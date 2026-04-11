from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from purchase_entrys.models import PurchaseRequisitionItem, PurchaseOrder, GRN, SRN, GRNItem, PurchaseOrderItem, SRNItem

class PendingPRReportView(APIView):

    def get(self, request):

        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        company = request.GET.get('company')
        project = request.GET.get('project')
        status = request.GET.get('status')  # optional

        queryset = PurchaseRequisitionItem.objects.select_related(
            'purchase_requisition',
            'purchase_requisition__company',
            'purchase_requisition__project'
        )


        queryset = queryset.filter(
            purchase_requisition__status='approved'   # PR approved
        )

        # FILTERS
        if from_date and to_date:
            queryset = queryset.filter(purchase_requisition__requisition_date__range=[from_date, to_date])

        if company:
            queryset = queryset.filter(purchase_requisition__company_id=company)

        if project:
            queryset = queryset.filter(purchase_requisition__project_id=project)

        if status:
            queryset = queryset.filter(purchase_requisition__status=status)

        data = []

        for obj in queryset:

            pr = obj.purchase_requisition
            data.append({
                "company": pr.company.name,
                "project": pr.project.name,
                "pr_no": pr.pr_number,
                "date": pr.requisition_date,
                "type": pr.requisition_type,
                "requisition_for": pr.requisition_for,
                "reference_so": getattr(getattr(pr, 'reference_so', None), 'so_number', None),
                "item_code": getattr(getattr(obj, 'item', None), 'code', ''),
                "item_name": getattr(getattr(obj, 'item', None), 'name', obj.product_name),
            })

        return Response(data)
    
# Complete PR
class CompletePRReportView(APIView):

    def get(self, request):

        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        company = request.GET.get('company')
        project = request.GET.get('project')
        status = request.GET.get('status')

        queryset = PurchaseRequisitionItem.objects.select_related(
            'purchase_requisition',
            'purchase_requisition__company',
            'purchase_requisition__project'
        )

        # 🔥 COMPLETE CONDITION
        queryset = queryset.filter(
            purchase_requisition__status='po_raised'
        )

        # FILTERS
        if from_date and to_date:
            queryset = queryset.filter(
                purchase_requisition__requisition_date__range=[from_date, to_date]
            )

        if company:
            queryset = queryset.filter(
                purchase_requisition__company_id=company
            )

        if project:
            queryset = queryset.filter(
                purchase_requisition__project_id=project
            )

        if status:
            queryset = queryset.filter(
                purchase_requisition__status=status
            )

        data = []

        for obj in queryset:

            pr = obj.purchase_requisition

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

                "item_code": getattr(getattr(obj, 'item', None), 'code', ''),
                "item_name": getattr(getattr(obj, 'item', None), 'name', obj.product_name),
            })

        return Response(data)
    
# PO Report
class POReportView(APIView):

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

        return Response(data)
    

# Complete GRN
class CompleteGRNReportView(APIView):

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
        ).prefetch_related(
            'items'
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

            for item in GRNItem.objects.filter(grn=grn):

                # 🔥 GET PO QTY
                po_item = PurchaseOrderItem.objects.filter(
                    purchase_order=grn.po,
                    product__product_name=item.product_name
                ).first()

                po_qty = po_item.qty if po_item else item.order_qty

                accepted = item.received_qty or 0
                rejected = getattr(item, 'rejected_qty', 0) or 0

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

                    "item_code": getattr(getattr(po_item, 'product', None), 'pk', ''),
                    "item_name": item.product_name,

                    "po_qty": po_qty,
                    "accepted_qty": accepted,
                    "rejected_qty": rejected,
                    "pending_qty": pending,

                    "uom": item.uom,
                    "rate": item.rate,

                    "total_value": item.amount,
                })

        return Response(data)
    
class PendingSRNReportView(APIView):

    def get(self, request):

        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        company = request.GET.get('company')
        project = request.GET.get('project')
        supplier = request.GET.get('supplier')

        po_items = PurchaseOrderItem.objects.select_related(
            'purchase_order',
            'purchase_order__company',
            'purchase_order__project',
            'purchase_order__supplier',
            'product'
        )

        if from_date and to_date:
            po_items = po_items.filter(purchase_order__entry_date__range=[from_date, to_date])

        if company:
            po_items = po_items.filter(purchase_order__company_id=company)

        if project:
            po_items = po_items.filter(purchase_order__project_id=project)

        if supplier:
            po_items = po_items.filter(purchase_order__supplier_id=supplier)

        data = []

        for po_item in po_items:

            # 🔥 TOTAL SRN RECEIVED
            received = SRNItem.objects.filter(
                srn__po=po_item.purchase_order,
                item__item_name=po_item.product.product_name
            ).aggregate(total=Sum('received_qty'))['total'] or 0

            pending = po_item.qty - received

            # ONLY PENDING
            if pending > 0:

                data.append({
                    "company": po_item.purchase_order.company.name,
                    "project_code": po_item.purchase_order.project.name,

                    "po_no": po_item.purchase_order.po_number,
                    "po_date": getattr(po_item.purchase_order, 'po_date', po_item.purchase_order.entry_date),
                    "po_type": po_item.purchase_order.po_type,

                    "vendor_code": po_item.purchase_order.supplier.gst_no or "",
                    "vendor_name": po_item.purchase_order.supplier.name,

                    "item_code": getattr(po_item.product, 'pk', ''),
                    "item_name": po_item.product.product_name,

                    "po_qty": po_item.qty,
                    "received_qty": received,
                    "pending_qty": pending,
                })

        return Response(data)
    
# Complete SRN
class CompleteSRNReportView(APIView):

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

        return Response(data)
