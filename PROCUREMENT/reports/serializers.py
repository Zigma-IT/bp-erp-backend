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
    qty = serializers.FloatField()
    uom = serializers.CharField(allow_blank=True)
    pending_qty = serializers.FloatField()
    remarks = serializers.CharField(allow_blank=True)
    prepared_by = serializers.CharField(allow_blank=True)
    prepared_date = serializers.DateTimeField(allow_null=True)
    authorized_by = serializers.CharField(allow_blank=True)
    authorized_date = serializers.DateTimeField(allow_null=True)
    authorized_status = serializers.CharField(allow_blank=True)

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
    qty = serializers.FloatField()
    uom = serializers.CharField(allow_blank=True)
    po_no = serializers.CharField(allow_blank=True)
    po_status = serializers.CharField(allow_blank=True)
    l1_action_by_date = serializers.CharField(allow_blank=True)
    l2_action_by_date = serializers.CharField(allow_blank=True)
    l3_action_by_date = serializers.CharField(allow_blank=True)
    po_qty = serializers.FloatField()
    vendor_name = serializers.CharField(allow_blank=True)
    grn_srn_number = serializers.CharField(allow_blank=True)
    grn_srn_date = serializers.CharField(allow_blank=True)
    prepared_by = serializers.CharField(allow_blank=True)
    prepared_date = serializers.DateTimeField(allow_null=True)
    authorized_by = serializers.CharField(allow_blank=True)
    authorized_date = serializers.DateTimeField(allow_null=True)
    authorized_status = serializers.CharField(allow_blank=True)

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
    ref_so_no = serializers.CharField(allow_blank=True, allow_null=True)
    linked_pr_no = serializers.CharField(allow_blank=True, allow_null=True)
    quotation_no = serializers.CharField(allow_blank=True, allow_null=True)
    prepared_by = serializers.CharField(allow_blank=True, allow_null=True)
    prepared_date = serializers.DateTimeField(allow_null=True)
    authorized_by = serializers.CharField(allow_blank=True, allow_null=True)
    authorized_date = serializers.DateTimeField(allow_null=True)
    grn_srn_number = serializers.CharField(allow_blank=True, allow_null=True)
    grn_srn_date = serializers.CharField(allow_blank=True, allow_null=True)
    status = serializers.CharField(allow_blank=True, allow_null=True)


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
    uom = serializers.CharField(allow_blank=True)
    rate = serializers.FloatField()
    total_value = serializers.FloatField()
    grn_no = serializers.CharField(allow_blank=True)
    grn_date = serializers.CharField(allow_blank=True)
    status = serializers.CharField(allow_blank=True)


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
    prepared_by_dt = serializers.CharField(allow_blank=True)
    checked_by = serializers.CharField(allow_blank=True)
    authorized_by_dt = serializers.CharField(allow_blank=True)
    status = serializers.CharField(allow_blank=True)


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
    uom = serializers.CharField(allow_blank=True)
    rate = serializers.FloatField()
    amount = serializers.FloatField()
    srn_no = serializers.CharField(allow_blank=True)
    srn_date = serializers.CharField(allow_blank=True)
    status = serializers.CharField(allow_blank=True)

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
    item_code = serializers.CharField()
    item_name = serializers.CharField()
    po_qty = serializers.FloatField()
    accepted_qty = serializers.FloatField()
    rejected_qty = serializers.FloatField()
    pending_qty = serializers.FloatField()
    uom = serializers.CharField(allow_blank=True)
    rate = serializers.FloatField()
    total_value = serializers.FloatField()
    prepared_by_dt = serializers.CharField(allow_blank=True)
    checked_by = serializers.CharField(allow_blank=True)
    authorized_by_dt = serializers.CharField(allow_blank=True)
    status = serializers.CharField(allow_blank=True)
