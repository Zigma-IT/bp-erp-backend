from rest_framework import serializers

from purchase_entrys.models import GRN, PurchaseRequisition, SRN
from sales.models import SalesOrder, SalesOrderItem, SalesInvoice, SalesInvoiceItem

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
    approval_status = serializers.CharField(source='status', read_only=True)

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
            'requisition_date',
            'requested_by',
            'status',
            'approval_status',
        ]
        read_only_fields = [
            'id',
            'company',
            'company_name',
            'project',
            'project_name',
            'pr_number',
            'requisition_for',
            'requisition_type',
            'requisition_date',
            'requested_by',
            'status',
            'approval_status',
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


# Sales Invoice Approvals
class SalesInvoiceApprovalItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.product_name", read_only=True)
    uom = serializers.CharField(source="unit.unit_name", read_only=True)

    class Meta:
        model = SalesInvoiceItem
        fields = [
            "id",
            "product_name",
            "uom",
            "qty",
            "rate",
            "discount_type",
            "discount_percent",
            "tax_percent",
            "amount",
            "remarks",
        ]


class SalesInvoiceApprovalDetailSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    items = SalesInvoiceApprovalItemSerializer(many=True, read_only=True)

    class Meta:
        model = SalesInvoice
        fields = [
            "id",
            "invoice_date",
            "payment_due_date",
            "invoice_number",
            "remarks",
            "status",
            "company",
            "company_name",
            "customer",
            "customer_name",
            "created_at",
            "items",
        ]


class SalesInvoiceApprovalListRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sno = serializers.IntegerField()
    invoice_date = serializers.DateField()
    invoice_number = serializers.CharField()
    company_name = serializers.CharField()
    customer_name = serializers.CharField()
    amount = serializers.CharField()
    approve_status = serializers.CharField()


# Sales Invoice Create/Update
class SalesInvoiceItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesInvoiceItem
        fields = [
            "id",
            "product",
            "unit",
            "qty",
            "rate",
            "discount_type",
            "discount_percent",
            "tax_percent",
            "amount",
            "remarks",
        ]


class SalesInvoiceCreateUpdateSerializer(serializers.ModelSerializer):
    items = SalesInvoiceItemWriteSerializer(many=True, required=False)

    class Meta:
        model = SalesInvoice
        fields = [
            "id",
            "invoice_date",
            "payment_due_date",
            "invoice_number",
            "remarks",
            "status",
            "company",
            "customer",
            "items",
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        invoice = SalesInvoice.objects.create(**validated_data)
        
        for item_data in items_data:
            SalesInvoiceItem.objects.create(sales_invoice=invoice, **item_data)
        
        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update items if provided
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                SalesInvoiceItem.objects.create(sales_invoice=instance, **item_data)
        
        return instance
