"""Schema serializers for report responses shown in swagger."""

from rest_framework import serializers


class PendingPRReportSerializer(serializers.Serializer):

    company = serializers.CharField()
    project = serializers.CharField()

    pr_no = serializers.CharField()
    date = serializers.DateField()

    type = serializers.CharField()
    requisition_for = serializers.CharField()

    reference_so = serializers.CharField(allow_blank=True, allow_null=True)

    item_code = serializers.CharField()
    item_name = serializers.CharField()

# Complete PR
class CompletePRReportSerializer(serializers.Serializer):

    unit = serializers.CharField()
    project_code = serializers.CharField()

    pr_no = serializers.CharField()
    pr_date = serializers.DateField()

    type = serializers.CharField()
    requisition_for = serializers.CharField()

    ref_so_no = serializers.CharField(allow_blank=True, allow_null=True)

    doc_status = serializers.CharField()
    item_status = serializers.CharField()

    item_code = serializers.CharField()
    item_name = serializers.CharField()

# PO Report
class POReportSerializer(serializers.Serializer):

    unit = serializers.CharField()
    project_code = serializers.CharField()

    po_no = serializers.CharField()
    po_date = serializers.DateField()

    po_type = serializers.CharField()

    vendor_code = serializers.CharField(allow_blank=True)
    vendor_name = serializers.CharField()

    currency = serializers.CharField()
    exchange_rate = serializers.FloatField()

    basic_value = serializers.FloatField()
    discount = serializers.FloatField()
    total_value = serializers.FloatField()


# Pending GRN
class PendingGRNReportSerializer(serializers.Serializer):

    company = serializers.CharField()
    project_code = serializers.CharField()

    po_no = serializers.CharField()
    po_date = serializers.DateField()
    po_type = serializers.CharField()

    vendor_code = serializers.CharField(allow_blank=True)
    vendor_name = serializers.CharField()

    item_code = serializers.CharField()
    item_name = serializers.CharField()

    po_qty = serializers.FloatField()
    received_qty = serializers.FloatField()
    pending_qty = serializers.FloatField()


# Complete GRN
class CompleteGRNReportSerializer(serializers.Serializer):

    grn_no = serializers.CharField()
    grn_date = serializers.DateField()

    company = serializers.CharField()
    project = serializers.CharField()

    vendor_name = serializers.CharField()

    supplier_invoice = serializers.CharField()
    invoice_date = serializers.DateField()

    challan_no = serializers.CharField(allow_blank=True, allow_null=True)
    eway_bill_no = serializers.CharField(allow_blank=True, allow_null=True)
    po_no = serializers.CharField(allow_blank=True, allow_null=True)

    item_code = serializers.CharField()
    item_name = serializers.CharField()

    po_qty = serializers.FloatField()
    accepted_qty = serializers.FloatField()
    rejected_qty = serializers.FloatField()
    pending_qty = serializers.FloatField()

    uom = serializers.CharField()
    rate = serializers.FloatField()
    total_value = serializers.FloatField()


# Pending SRN
class PendingSRNReportSerializer(serializers.Serializer):

    company = serializers.CharField()
    project_code = serializers.CharField()

    po_no = serializers.CharField()
    po_date = serializers.DateField()
    po_type = serializers.CharField()

    vendor_code = serializers.CharField(allow_blank=True)
    vendor_name = serializers.CharField()

    item_code = serializers.CharField()
    item_name = serializers.CharField()

    po_qty = serializers.FloatField()
    received_qty = serializers.FloatField()
    pending_qty = serializers.FloatField()

# Complete SRN
class CompleteSRNReportSerializer(serializers.Serializer):

    srn_no = serializers.CharField()
    srn_date = serializers.DateField()

    unit = serializers.CharField()
    project = serializers.CharField()

    vendor_name = serializers.CharField()

    supplier_invoice = serializers.CharField()
    invoice_date = serializers.DateField()

    challan_no = serializers.CharField(allow_blank=True, allow_null=True)
    eway_bill_no = serializers.CharField(allow_blank=True, allow_null=True)
    transport_details = serializers.CharField(allow_blank=True, allow_null=True)
    po_no = serializers.CharField(allow_blank=True, allow_null=True)
