"""Database models for procurement entry transactions and approval workflow."""

import uuid

from decimal import Decimal

from django.db import models
from django.utils import timezone
from common_master.models import Company as CompanyMaster
from common_master.models import Project as ProjectMaster
from common_master.models import Tax as TaxMaster

class UniqueIDMixin(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        abstract = True


# Rate order
class RateOrder(UniqueIDMixin):

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)

    # Line rows are stored on the header so procurement no longer needs a
    # separate rate-order line table.
    items_data = models.JSONField(default=list, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RateOrder-{self.pk}"


class Supplier(UniqueIDMixin):
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

    class Meta(UniqueIDMixin.Meta):
        ordering = ["name"]

    def __str__(self):
        return self.name

# Purchase Order
class PurchaseOrder(UniqueIDMixin):
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

    # Purchase-order lines live in JSON on the header so the API still exposes
    # an `items` array without maintaining a separate item table.
    items_data = models.JSONField(default=list, blank=True)

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

    class Meta(UniqueIDMixin.Meta):
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


class PurchaseOrderApproval(UniqueIDMixin):
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

    class Meta(UniqueIDMixin.Meta):
        unique_together = ("purchase_order", "level")
        ordering = ["purchase_order_id", "level"]

    def __str__(self):
        try:
            level_label = self.Level(self.level).label
        except ValueError:
            level_label = str(self.level)
        return f"{self.purchase_order} - {level_label}"

# Purchase requisition


class PurchaseRequisition(UniqueIDMixin):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('foreclosed', 'Foreclosed'),
        ('po_raised', 'PO Raised'),
    )
    APPROVAL_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    pr_number = models.CharField(max_length=100, unique=True, blank=True)

    company = models.ForeignKey(CompanyMaster, on_delete=models.CASCADE)
    project = models.ForeignKey(ProjectMaster, on_delete=models.CASCADE)

    requisition_for = models.CharField(max_length=100)   # Direct / Indirect
    requisition_type = models.CharField(max_length=100)  # Regular / Service

    requisition_date = models.DateField()
    items_data = models.JSONField(default=list, blank=True)

    requested_by = models.CharField(max_length=255)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    level1_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
    )
    level1_approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_requisition_level1_approved',
    )
    level1_approved_at = models.DateTimeField(null=True, blank=True)
    level1_remarks = models.TextField(blank=True, null=True)
    level2_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
    )
    level2_approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_requisition_level2_approved',
    )
    level2_approved_at = models.DateTimeField(null=True, blank=True)
    level2_remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.pr_number

    def generate_pr_number(self):
        requisition_date = self.requisition_date or timezone.localdate()
        fy_start = (
            requisition_date.year
            if requisition_date.month >= 4
            else requisition_date.year - 1
        )
        fy_end = fy_start + 1
        company_code = (self.company.code or "GEN").upper()
        prefix = f"PR/{fy_start}-{fy_end}/{company_code}"

        last_pr_number = (
            PurchaseRequisition.objects.filter(pr_number__startswith=prefix)
            .order_by("-id")
            .values_list("pr_number", flat=True)
            .first()
        )

        next_number = 1
        if last_pr_number:
            try:
                next_number = int(last_pr_number.rsplit("/", 1)[1]) + 1
            except (IndexError, ValueError):
                next_number = PurchaseRequisition.objects.filter(
                    pr_number__startswith=prefix
                ).count() + 1

        return f"{prefix}/{next_number:03d}"

    def save(self, *args, **kwargs):
        try:
            company = self.company
        except CompanyMaster.DoesNotExist:
            company = None
        if not self.pr_number and company and company.pk is not None:
            self.pr_number = self.generate_pr_number()
        super().save(*args, **kwargs)


class GRN(UniqueIDMixin):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('checked', 'Checked'),
        ('rejected', 'Rejected'),
    )
    APPROVAL_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    grn_number = models.CharField(max_length=100, unique=True, blank=True)

    company = models.ForeignKey(CompanyMaster, on_delete=models.CASCADE)
    project = models.ForeignKey(ProjectMaster, on_delete=models.CASCADE)

    po = models.ForeignKey('PurchaseOrder', on_delete=models.CASCADE)

    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)
    items_data = models.JSONField(default=list, blank=True)

    invoice_date = models.DateField()
    supplier_invoice_no = models.CharField(max_length=100)

    eway_bill_no = models.CharField(max_length=100, blank=True, null=True)
    eway_bill_date = models.DateField(blank=True, null=True)

    dc_no = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    level1_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
    )
    level1_approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grn_level1_approved',
    )
    level1_approved_at = models.DateTimeField(null=True, blank=True)
    level1_remarks = models.TextField(blank=True, null=True)
    level2_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
    )
    level2_checked_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grn_level2_checked',
    )
    level2_checked_at = models.DateTimeField(null=True, blank=True)
    level2_remarks = models.TextField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.grn_number

    def generate_grn_number(self):
        invoice_date = self.invoice_date or timezone.localdate()
        fy_start = invoice_date.year if invoice_date.month >= 4 else invoice_date.year - 1
        fy_end = fy_start + 1
        company_code = (self.company.code or "GEN").upper()
        prefix = f"GRN/{fy_start}-{fy_end}/{company_code}"

        last_grn_number = (
            GRN.objects.filter(grn_number__startswith=prefix)
            .order_by("-id")
            .values_list("grn_number", flat=True)
            .first()
        )

        next_number = 1
        if last_grn_number:
            try:
                next_number = int(last_grn_number.rsplit("/", 1)[1]) + 1
            except (IndexError, ValueError):
                next_number = GRN.objects.filter(
                    grn_number__startswith=prefix
                ).count() + 1

        return f"{prefix}/{next_number:03d}"

    def save(self, *args, **kwargs):
        try:
            company = self.company
        except CompanyMaster.DoesNotExist:
            company = None
        if not self.grn_number and company and company.pk is not None:
            self.grn_number = self.generate_grn_number()
        super().save(*args, **kwargs)


class SRN(UniqueIDMixin):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('checked', 'Checked'),
        ('rejected', 'Rejected'),
    )
    APPROVAL_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    srn_number = models.CharField(max_length=100, unique=True, blank=True)

    company = models.ForeignKey(CompanyMaster, on_delete=models.CASCADE)
    project = models.ForeignKey(ProjectMaster, on_delete=models.CASCADE)

    po = models.ForeignKey('PurchaseOrder', on_delete=models.CASCADE)
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)
    items_data = models.JSONField(default=list, blank=True)

    # 🔹 Dates
    po_date = models.DateField(null=True, blank=True)
    invoice_date = models.DateField()
    tax_invoice_date = models.DateField(null=True, blank=True)

    # 🔹 Invoice
    supplier_invoice_no = models.CharField(max_length=100)
    tax_invoice_no = models.CharField(max_length=100, blank=True, null=True)

    # 🔹 Logistics
    eway_bill_no = models.CharField(max_length=100, blank=True, null=True)
    eway_bill_date = models.DateField(blank=True, null=True)

    dc_no = models.CharField(max_length=100, blank=True, null=True)
    delivery_challan_no = models.CharField(max_length=100, blank=True, null=True)

    vehicle_no = models.CharField(max_length=100, blank=True, null=True)
    transporter = models.CharField(max_length=255, blank=True, null=True)

    received_at = models.CharField(max_length=255)

    # 🔹 Compliance / Flags
    original_invoice = models.BooleanField(default=False)
    oem_manual = models.BooleanField(default=False)
    delivery_challan = models.BooleanField(default=False)
    test_certificate = models.BooleanField(default=False)

    # 🔹 Additional
    amd_no = models.CharField(max_length=100, blank=True, null=True)
    cost_center = models.CharField(max_length=100, blank=True, null=True)

    # 🔹 Charges (Header Level)
    basic = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    paf = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    freight_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    other_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    total_gst = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    round_off = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    # 🔹 Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    level1_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
    )
    level1_approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='srn_level1_approved',
    )
    level1_approved_at = models.DateTimeField(null=True, blank=True)
    level1_remarks = models.TextField(blank=True, null=True)
    level2_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
    )
    level2_approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='srn_level2_approved',
    )
    level2_approved_at = models.DateTimeField(null=True, blank=True)
    level2_remarks = models.TextField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.srn_number

    def generate_srn_number(self):
        invoice_date = self.invoice_date or timezone.localdate()
        fy_start = invoice_date.year if invoice_date.month >= 4 else invoice_date.year - 1
        fy_end = fy_start + 1
        company_code = (self.company.code or "GEN").upper()
        prefix = f"SRN/{fy_start}-{fy_end}/{company_code}"

        last_srn_number = (
            SRN.objects.filter(srn_number__startswith=prefix)
            .order_by("-id")
            .values_list("srn_number", flat=True)
            .first()
        )

        next_number = 1
        if last_srn_number:
            try:
                next_number = int(last_srn_number.rsplit("/", 1)[1]) + 1
            except (IndexError, ValueError):
                next_number = SRN.objects.filter(
                    srn_number__startswith=prefix
                ).count() + 1

        return f"{prefix}/{next_number:03d}"

    def save(self, *args, **kwargs):
        try:
            company = self.company
        except CompanyMaster.DoesNotExist:
            company = None
        if not self.srn_number and company and company.pk is not None:
            self.srn_number = self.generate_srn_number()
        super().save(*args, **kwargs)
    
class SRNItem(UniqueIDMixin):

    srn = models.ForeignKey(SRN, related_name='items', on_delete=models.CASCADE)

    item = models.ForeignKey(ItemMaster, on_delete=models.CASCADE)

    order_qty = models.DecimalField(max_digits=10, decimal_places=2)
    previously_received_qty = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    received_qty = models.DecimalField(max_digits=10, decimal_places=2)

    rate = models.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2)

    discount_type = models.CharField(max_length=50, blank=True, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    remarks = models.TextField(blank=True, null=True)
    