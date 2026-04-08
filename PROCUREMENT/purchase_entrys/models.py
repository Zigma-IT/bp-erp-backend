from decimal import Decimal

from django.db import models
from django.utils import timezone
from common_master.models import Company as CompanyMaster
from common_master.models import Project as ProjectMaster
from common_master.models import Tax as TaxMaster
from purchase_master.models import ProductCreation as ProductMaster
from purchase_master.models import UnitMaster


class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    gst_no = models.CharField(max_length=20, blank=True, null=True)
    pan_no = models.CharField(max_length=20, blank=True, null=True)
    msme_type = models.CharField(max_length=100, blank=True, null=True)
    msme_no = models.CharField(max_length=50, blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    contact_no = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    class WorkflowStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_L1 = "pending_l1", "Pending (L1)"
        APPROVED_L1 = "approved_l1", "Approved (L1)"
        REJECTED_L1 = "rejected_l1", "Rejected (L1)"
        APPROVED_L2 = "approved_l2", "Approved (L2)"
        REJECTED_L2 = "rejected_l2", "Rejected (L2)"
        APPROVED_L3 = "approved_l3", "Approved (L3)"
        REJECTED_L3 = "rejected_l3", "Rejected (L3)"

    po_number = models.CharField(max_length=100, unique=True, blank=True)
    company = models.ForeignKey(
        CompanyMaster,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    project = models.ForeignKey(
        ProjectMaster,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )

    po_type = models.CharField(max_length=50, blank=True, null=True)
    pr_number = models.CharField(max_length=100, blank=True, null=True)
    from_company = models.BooleanField(default=False)
    entry_date = models.DateField(default=timezone.localdate)

    # Snapshot fields copied from supplier/project masters so the PO keeps the
    # values that were used when the order was created.
    supplier_gst_no = models.CharField(max_length=20, blank=True, null=True)
    supplier_pan_no = models.CharField(max_length=20, blank=True, null=True)
    supplier_msme_type = models.CharField(max_length=100, blank=True, null=True)
    supplier_msme_no = models.CharField(max_length=50, blank=True, null=True)
    supplier_contact_person = models.CharField(max_length=255, blank=True, null=True)
    supplier_contact_no = models.CharField(max_length=20, blank=True, null=True)

    quotation_no = models.CharField(max_length=100, blank=True, null=True)
    quotation_date = models.DateField(blank=True, null=True)

    revision_no = models.CharField(max_length=50, default="REV001")
    revision_date = models.DateField(blank=True, null=True)
    revision_remarks = models.TextField(blank=True, null=True)

    total_basic_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    freight_charges = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    freight_tax = models.ForeignKey(
        TaxMaster,
        on_delete=models.PROTECT,
        related_name="freight_purchase_orders",
        blank=True,
        null=True,
    )
    freight_tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    other_charges = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    other_tax = models.ForeignKey(
        TaxMaster,
        on_delete=models.PROTECT,
        related_name="other_charge_purchase_orders",
        blank=True,
        null=True,
    )
    other_tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    packing_forwarding = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    packing_tax = models.ForeignKey(
        TaxMaster,
        on_delete=models.PROTECT,
        related_name="packing_purchase_orders",
        blank=True,
        null=True,
    )
    packing_tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    round_off = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total_gst_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    payment_days = models.CharField(max_length=255, blank=True, null=True)
    other_terms_conditions = models.TextField(blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    workflow_status = models.CharField(
        max_length=20,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.PENDING_L1,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-entry_date", "-id"]

    def __str__(self):
        return self.po_number or f"PO-{self.pk}"

    @property
    def approval_status_label(self):
        try:
            return self.WorkflowStatus(self.workflow_status).label
        except ValueError:
            return str(self.workflow_status)

    def clean_snapshot_fields(self):
        try:
            supplier = self.supplier
        except Supplier.DoesNotExist:
            return
        if supplier.pk is None:
            return

        self.supplier_gst_no = self.supplier_gst_no or (supplier.gst_no or "")
        self.supplier_pan_no = self.supplier_pan_no or (supplier.pan_no or "")
        self.supplier_msme_type = self.supplier_msme_type or (supplier.msme_type or "")
        self.supplier_msme_no = self.supplier_msme_no or (supplier.msme_no or "")
        self.supplier_contact_person = self.supplier_contact_person or (
            supplier.contact_person or ""
        )
        self.supplier_contact_no = self.supplier_contact_no or (
            supplier.contact_no or ""
        )

    def generate_po_number(self):
        entry_date = self.entry_date or timezone.localdate()
        fy_start = entry_date.year if entry_date.month >= 4 else entry_date.year - 1
        fy_end = fy_start + 1
        company_code = (self.company.code or "GEN").upper()
        prefix = f"PO/{fy_start}-{fy_end}/{company_code}"

        last_po_number = (
            PurchaseOrder.objects.filter(po_number__startswith=prefix)
            .order_by("-id")
            .values_list("po_number", flat=True)
            .first()
        )

        next_number = 1
        if last_po_number:
            try:
                next_number = int(last_po_number.rsplit("/", 1)[1]) + 1
            except (IndexError, ValueError):
                next_number = PurchaseOrder.objects.filter(
                    po_number__startswith=prefix
                ).count() + 1

        return f"{prefix}/{next_number:03d}"

    def sync_workflow_status(self):
        approvals = {
            approval.level: approval
            for approval in PurchaseOrderApproval.objects.filter(purchase_order_id=self.pk)
        }
        level_1 = approvals.get(PurchaseOrderApproval.Level.LEVEL_1)
        level_2 = approvals.get(PurchaseOrderApproval.Level.LEVEL_2)
        level_3 = approvals.get(PurchaseOrderApproval.Level.LEVEL_3)

        if level_3 and level_3.status == PurchaseOrderApproval.Status.APPROVED:
            new_status = self.WorkflowStatus.APPROVED_L3
        elif level_3 and level_3.status == PurchaseOrderApproval.Status.REJECTED:
            new_status = self.WorkflowStatus.REJECTED_L3
        elif level_2 and level_2.status == PurchaseOrderApproval.Status.APPROVED:
            new_status = self.WorkflowStatus.APPROVED_L2
        elif level_2 and level_2.status == PurchaseOrderApproval.Status.REJECTED:
            new_status = self.WorkflowStatus.REJECTED_L2
        elif level_1 and level_1.status == PurchaseOrderApproval.Status.APPROVED:
            new_status = self.WorkflowStatus.APPROVED_L1
        elif level_1 and level_1.status == PurchaseOrderApproval.Status.REJECTED:
            new_status = self.WorkflowStatus.REJECTED_L1
        else:
            new_status = self.WorkflowStatus.PENDING_L1

        if self.workflow_status != new_status:
            self.workflow_status = new_status
            self.save(update_fields=["workflow_status", "updated_at"])

    def save(self, *args, **kwargs):
        self.clean_snapshot_fields()
        try:
            company = self.company
        except CompanyMaster.DoesNotExist:
            company = None
        if not self.po_number and company and company.pk is not None:
            self.po_number = self.generate_po_number()
        super().save(*args, **kwargs)


class PurchaseOrderItem(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage"
        AMOUNT = "amount", "Amount"

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        related_name="items",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        ProductMaster,
        on_delete=models.PROTECT,
        related_name="purchase_order_items",
    )
    unit = models.ForeignKey(
        UnitMaster,
        on_delete=models.PROTECT,
        related_name="purchase_order_items",
    )
    qty = models.DecimalField(max_digits=12, decimal_places=2)
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    tax = models.ForeignKey(
        TaxMaster,
        on_delete=models.PROTECT,
        related_name="purchase_order_items",
        blank=True,
        null=True,
    )
    tax_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    delivery_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        purchase_order_pk = self.purchase_order.pk if self.purchase_order else None
        return f"{purchase_order_pk} - {self.product}"


class PurchaseOrderApproval(models.Model):
    class Level(models.IntegerChoices):
        LEVEL_1 = 1, "Level 1"
        LEVEL_2 = 2, "Level 2"
        LEVEL_3 = 3, "Level 3"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="approvals",
    )
    level = models.PositiveSmallIntegerField(choices=Level.choices)
    approved_net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    approved_gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    remarks = models.TextField(blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("purchase_order", "level")
        ordering = ["purchase_order_id", "level"]

    def __str__(self):
        try:
            level_label = self.Level(self.level).label
        except ValueError:
            level_label = str(self.level)
        return f"{self.purchase_order} - {level_label}"
