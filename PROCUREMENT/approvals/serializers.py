from rest_framework import serializers

from purchase_entrys.models import GRN, PurchaseRequisition, SRN
from sales.models import SalesOrder, SalesOrderItem

# Sales order approvals
class SalesOrderApprovalItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    uom = serializers.CharField(source="unit.unit_name", read_only=True)

    class Meta:
        model = SalesOrderItem
        fields = [
            "id",
            "product_name",
            "uom",
            "qty",
            "rate",
            "tax_percent",
            "amount",
            "sub_task",
        ]


class SalesOrderApprovalDetailSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    items = SalesOrderApprovalItemSerializer(many=True, read_only=True)

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


# Purchase Requisition Approval Level 1


class PRApprovalLevel1Serializer(serializers.ModelSerializer):

    company_name = serializers.CharField(source='company.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

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
    requested_by = serializers.CharField(source='created_by.username', read_only=True)

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

# GRN Approval Level 1
class GRNApprovalLevel1Serializer(serializers.ModelSerializer):

    company_name = serializers.CharField(source='company.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

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
