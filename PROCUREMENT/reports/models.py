"""Database models for stored procurement report snapshots.

Each report API still calculates live data from procurement transactions, then
stores the generated rows here as the latest snapshot for the same filter set.
This gives the frontend/API response live values while also keeping report data
available in the database for checking and auditing.
"""

import uuid
from decimal import Decimal
from django.db import models


class ReportSnapshotMixin(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    filter_signature = models.CharField(max_length=64, db_index=True)
    filter_params = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["-generated_at", "id"]


class PendingPRReport(ReportSnapshotMixin):
    company = models.CharField(max_length=255)
    project = models.CharField(max_length=255)
    pr_no = models.CharField(max_length=100)
    date = models.DateField()
    type = models.CharField(max_length=100)
    requisition_for = models.CharField(max_length=100)
    reference_so = models.CharField(max_length=100, blank=True, null=True)
    item_code = models.CharField(max_length=100, blank=True)
    item_name = models.CharField(max_length=255)


class CompletePRReport(ReportSnapshotMixin):
    unit = models.CharField(max_length=255)
    project_code = models.CharField(max_length=255)
    pr_no = models.CharField(max_length=100)
    pr_date = models.DateField()
    type = models.CharField(max_length=100)
    requisition_for = models.CharField(max_length=100)
    ref_so_no = models.CharField(max_length=100, blank=True, null=True)
    doc_status = models.CharField(max_length=100)
    item_status = models.CharField(max_length=100)
    item_code = models.CharField(max_length=100, blank=True)
    item_name = models.CharField(max_length=255)


class POReport(ReportSnapshotMixin):
    unit = models.CharField(max_length=255)
    project_code = models.CharField(max_length=255)
    po_no = models.CharField(max_length=100)
    po_date = models.DateField()
    po_type = models.CharField(max_length=100, blank=True, null=True)
    vendor_code = models.CharField(max_length=100, blank=True)
    vendor_name = models.CharField(max_length=255)
    currency = models.CharField(max_length=50, blank=True)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("0.00"))
    basic_value = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))


class PendingGRNReport(ReportSnapshotMixin):
    company = models.CharField(max_length=255)
    project_code = models.CharField(max_length=255)
    po_no = models.CharField(max_length=100)
    po_date = models.DateField()
    po_type = models.CharField(max_length=100, blank=True, null=True)
    vendor_code = models.CharField(max_length=100, blank=True)
    vendor_name = models.CharField(max_length=255)
    item_code = models.CharField(max_length=100, blank=True)
    item_name = models.CharField(max_length=255)
    po_qty = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    received_qty = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    pending_qty = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))


class CompleteGRNReport(ReportSnapshotMixin):
    grn_no = models.CharField(max_length=100)
    grn_date = models.DateField()
    company = models.CharField(max_length=255)
    project = models.CharField(max_length=255)
    vendor_name = models.CharField(max_length=255)
    supplier_invoice = models.CharField(max_length=100)
    invoice_date = models.DateField()
    challan_no = models.CharField(max_length=100, blank=True, null=True)
    eway_bill_no = models.CharField(max_length=100, blank=True, null=True)
    po_no = models.CharField(max_length=100, blank=True, null=True)
    item_code = models.CharField(max_length=100, blank=True)
    item_name = models.CharField(max_length=255)
    po_qty = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    accepted_qty = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    rejected_qty = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    pending_qty = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    uom = models.CharField(max_length=50, blank=True)
    rate = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))


class PendingSRNReport(ReportSnapshotMixin):
    company = models.CharField(max_length=255)
    project_code = models.CharField(max_length=255)
    po_no = models.CharField(max_length=100)
    po_date = models.DateField()
    po_type = models.CharField(max_length=100, blank=True, null=True)
    vendor_code = models.CharField(max_length=100, blank=True)
    vendor_name = models.CharField(max_length=255)
    item_code = models.CharField(max_length=100, blank=True)
    item_name = models.CharField(max_length=255)
    po_qty = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    received_qty = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    pending_qty = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))


class CompleteSRNReport(ReportSnapshotMixin):
    srn_no = models.CharField(max_length=100)
    srn_date = models.DateField()
    unit = models.CharField(max_length=255)
    project = models.CharField(max_length=255)
    vendor_name = models.CharField(max_length=255)
    supplier_invoice = models.CharField(max_length=100)
    invoice_date = models.DateField()
    challan_no = models.CharField(max_length=100, blank=True, null=True)
    eway_bill_no = models.CharField(max_length=100, blank=True, null=True)
    transport_details = models.CharField(max_length=255, blank=True, null=True)
    po_no = models.CharField(max_length=100, blank=True, null=True)
