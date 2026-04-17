"""Serializers used by procurement approval screens and swagger responses."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from purchase_entrys.models import GRN, PurchaseRequisition, SRN
from sales.models import SalesOrder


# Purchase Requisition Approval Level 1


class PRApprovalLevel1Serializer(serializers.ModelSerializer):

    company_name = serializers.CharField(source='company.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    req_date = serializers.DateField(source='requisition_date', read_only=True)

    class Meta:
        model = PurchaseRequisition
        fields = [
            'id',
            'pr_number',
            'company',
            'company_name',
            'project',
            'project_name',
            'requisition_for',
            'requisition_type',
            'req_date',


            'level1_status',
            'level1_approved_by',
            'level1_approved_at',
            'level1_remarks',
        ]


# Purchase Requisition Approval Level 2
class PRApprovalLevel2Serializer(serializers.ModelSerializer):

    company_name = serializers.CharField(source='company.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    req_date = serializers.DateField(source='requisition_date', read_only=True)
    requested_by = serializers.CharField(read_only=True)

    class Meta:
        model = PurchaseRequisition
        fields = [
            'id',
            'pr_number',
            'company_name',
            'project_name',
            'requisition_for',
            'requisition_type',
            'req_date',
            'requested_by',

            # Level 1 (read-only)
            'level1_status',

            # Level 2 (new)
            'level2_status',
            'level2_approved_by',
            'level2_approved_at',
            'level2_remarks',
        ]

# >>>>>>>>>>>>>>>>>>>> Purchase order approvals level 1 <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# serializers.py

from .models import PurchaseOrder, PurchaseOrderApproval

class PurchaseOrderApprovalListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    net_amount = serializers.DecimalField(
        source="total_basic_value",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    approval_level_1_status = serializers.SerializerMethodField()
    approval_level_2_status = serializers.SerializerMethodField()
    approval_level_3_status = serializers.SerializerMethodField()
    status = serializers.CharField(source="workflow_status", read_only=True)

    def _approval_status(self, obj, level):
        approval = next(
            (item for item in getattr(obj, "approvals").all() if item.level == level),
            None,
        )
        return approval.status if approval else PurchaseOrderApproval.Status.PENDING

    def get_approval_level_1_status(self, obj):
        return self._approval_status(obj, PurchaseOrderApproval.Level.LEVEL_1)

    def get_approval_level_2_status(self, obj):
        return self._approval_status(obj, PurchaseOrderApproval.Level.LEVEL_2)

    def get_approval_level_3_status(self, obj):
        return self._approval_status(obj, PurchaseOrderApproval.Level.LEVEL_3)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "entry_date",
            "po_number",
            "company_name",
            "project_name",
            "supplier_name",
            "net_amount",
            "gross_amount",
            "approval_level_1_status",
            "approval_level_2_status",
            "approval_level_3_status",
            "status",
        ]


# GRN Approval Level 1
class GRNApprovalLevel1Serializer(serializers.ModelSerializer):

    company_name = serializers.CharField(source='company.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    po_number = serializers.CharField(source='po.po_number', read_only=True)

    class Meta:
        model = GRN
        fields = [
            'id',
            'company_name',
            'project_name',
            'supplier_name',
            'invoice_date',
            'po_number',
            'grn_number',
            'supplier_invoice_no',

            # 👇 approval fields only
            'level1_status',
            'level1_approved_by',
            'level1_approved_at',
            'level1_remarks',
        ]

# GRN Approval Level 2
class GRNApprovalLevel2Serializer(serializers.ModelSerializer):

    company_name = serializers.CharField(source='company.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    po_number = serializers.CharField(source='po.po_number', read_only=True)
    checked_by = serializers.CharField(source='level2_checked_by.username', read_only=True)

    class Meta:
        model = GRN
        fields = [
            'id',
            'company_name',
            'project_name',
            'supplier_name',
            'invoice_date',
            'po_number',
            'grn_number',
            'supplier_invoice_no',

            # dependency
            'level1_status',

            # level 2
            'level2_status',
            'checked_by',
            'level2_checked_at',
            'level2_remarks',
        ]

# GRN Approval Level 1
class SRNApprovalLevel1Serializer(serializers.ModelSerializer):

    company_name = serializers.CharField(source='company.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    po_number = serializers.CharField(source='po.po_number', read_only=True)

    class Meta:
        model = SRN
        fields = [
            'id',
            'company_name',
            'project_name',
            'supplier_name',
            'invoice_date',
            'po_number',
            'srn_number',
            'supplier_invoice_no',

            # approval
            'level1_status',
            'level1_approved_by',
            'level1_approved_at',
            'level1_remarks',
        ]


# SRN Approval Level 2
class SRNApprovalLevel2Serializer(serializers.ModelSerializer):

    company_name = serializers.CharField(source='company.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    po_number = serializers.CharField(source='po.po_number', read_only=True)

    class Meta:
        model = SRN
        fields = [
            'id',
            'company_name',
            'project_name',
            'supplier_name',
            'invoice_date',
            'po_number',
            'srn_number',
            'supplier_invoice_no',

            # Level 1 (for visibility only)
            'level1_status',

            # Level 2
            'level2_status',
            'level2_approved_by',
            'level2_approved_at',
            'level2_remarks',
        ]

# Sales order approvals

class SalesOrderApprovalLineSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    product_name = serializers.CharField()
    uom = serializers.CharField()
    qty = serializers.DecimalField(max_digits=10, decimal_places=2)
    rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    sub_task = serializers.CharField(required=False, allow_blank=True)


class SalesOrderApprovalDetailSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    items = serializers.SerializerMethodField()

    @extend_schema_field(SalesOrderApprovalLineSerializer(many=True))
    def get_items(self, obj):
        return SalesOrderApprovalLineSerializer(
            obj.items_data or [],
            many=True,
        ).data

    class Meta:
        model = SalesOrder
        fields = [
            "id",
            "entry_date",
            "so_number",
            "so_type",
            "currency",
            "exchange_rate",
            "contact_person",
            "customer_po_number",
            "customer_po_date",
            "active_status",
            "status",
            "company",
            "company_name",
            "customer",
            "customer_name",
            "created_at",
            "items",
        ]


class SalesOrderApprovalListRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sno = serializers.IntegerField()
    entry_date = serializers.DateField()
    sales_order_no = serializers.CharField()
    company_name = serializers.CharField()
    customer_name = serializers.CharField()
    so_type = serializers.CharField()
    active_status = serializers.CharField()
    approve_status = serializers.CharField()
