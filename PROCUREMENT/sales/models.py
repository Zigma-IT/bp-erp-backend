"""Database models for sales orders, invoices, BOMs, and expense workflows."""

import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from common_master.models import Company as CompanyMaster


class UniqueIDMixin(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        abstract = True


class Customer(UniqueIDMixin):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name



# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Sales Invoice >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class SalesInvoice(UniqueIDMixin):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
    )

    entry_date = models.DateField()
    due_date = models.DateField()

    company = models.ForeignKey(CompanyMaster, on_delete=models.CASCADE)
    project = models.ForeignKey('common_master.Project', on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    items_data = models.JSONField(default=list, blank=True)

    invoice_number = models.CharField(max_length=100, unique=True, blank=True)

    remarks = models.TextField(blank=True, null=True)

    basic_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_gst = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    round_off = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    created_at = models.DateTimeField(auto_now_add=True)

    def generate_invoice_number(self):
        entry_date = self.entry_date or timezone.localdate()
        fy_start = entry_date.year if entry_date.month >= 4 else entry_date.year - 1
        fy_end = fy_start + 1
        company_code = (self.company.code or "GEN").upper()

        prefix = f"INV/{fy_start}-{fy_end}/{company_code}"

        last = SalesInvoice.objects.filter(invoice_number__startswith=prefix)\
            .order_by('-id').values_list('invoice_number', flat=True).first()

        next_no = 1
        if last:
            try:
                next_no = int(last.split('/')[-1]) + 1
            except (IndexError, ValueError):
                next_no = SalesInvoice.objects.filter(invoice_number__startswith=prefix).count() + 1

        return f"{prefix}/{next_no:03d}"

    def save(self, *args, **kwargs):
        try:
            company = self.company
        except CompanyMaster.DoesNotExist:
            company = None
        if not self.invoice_number and company and company.pk is not None:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Sales order >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class SalesOrder(UniqueIDMixin):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    entry_date = models.DateField()
    company = models.ForeignKey(CompanyMaster, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    items_data = models.JSONField(default=list, blank=True)
    so_number = models.CharField(max_length=100, unique=True, blank=True)
    so_type = models.CharField(max_length=100)
    currency = models.CharField(max_length=50)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    customer_po_number = models.CharField(max_length=100, blank=True, null=True)
    customer_po_date = models.DateField(blank=True, null=True)
    active_status = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(UniqueIDMixin.Meta):
        ordering = ['-entry_date', '-id']

    def __str__(self):
        return self.so_number or f"SO-{self.pk}"

    def generate_so_number(self):
        entry_date = self.entry_date or timezone.localdate()
        fy_start = entry_date.year if entry_date.month >= 4 else entry_date.year - 1
        fy_end = fy_start + 1
        company_code = (self.company.code or "GEN").upper()
        prefix = f"SO/{fy_start}-{fy_end}/{company_code}"

        last_so_number = (
            SalesOrder.objects.filter(so_number__startswith=prefix)
            .order_by('-id')
            .values_list('so_number', flat=True)
            .first()
        )

        next_number = 1
        if last_so_number:
            try:
                next_number = int(last_so_number.rsplit('/', 1)[1]) + 1
            except (IndexError, ValueError):
                next_number = SalesOrder.objects.filter(
                    so_number__startswith=prefix
                ).count() + 1

        return f"{prefix}/{next_number:03d}"

    def save(self, *args, **kwargs):
        try:
            company = self.company
        except CompanyMaster.DoesNotExist:
            company = None
        if not self.so_number and company and company.pk is not None:
            self.so_number = self.generate_so_number()
        super().save(*args, **kwargs)

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Ordered BOM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class OrderedBOM(UniqueIDMixin):
    MATERIAL_TYPE = (
        ('with_material', 'With Materials'),
        ('without_material', 'Without Materials'),
    )

    company = models.ForeignKey(CompanyMaster, on_delete=models.CASCADE)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE)
    items_data = models.JSONField(default=list, blank=True)

    so_type = models.CharField(max_length=100)

    material_type = models.CharField(max_length=50, choices=MATERIAL_TYPE)

    created_at = models.DateTimeField(auto_now_add=True)

#>>>>>>>>>>>>>>>>>>>>>>>>>>> Purchase Expense >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class ExpenseEntry(UniqueIDMixin):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    company = models.ForeignKey(CompanyMaster, on_delete=models.CASCADE)
    project = models.ForeignKey('common_master.Project', on_delete=models.CASCADE)

    supplier = models.ForeignKey('purchase_entrys.Supplier', on_delete=models.SET_NULL, null=True, blank=True)
    items_data = models.JSONField(default=list, blank=True)

    manual_supplier_name = models.CharField(max_length=255, null=True, blank=True)

    # category = models.ForeignKey('expense_master.Category', on_delete=models.PROTECT)
    # sub_category = models.ForeignKey('expense_master.SubCategory', on_delete=models.PROTECT)

    payment_type = models.CharField(max_length=100)

    expense_date = models.DateField()

    expense_number = models.CharField(max_length=100, unique=True, blank=True)

    remarks = models.TextField(blank=True, null=True)

    basic_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_gst = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    round_off = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>Purchase Expense Approval <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

class ExpenseApprovalConfig(models.Model):
    company = models.ForeignKey(CompanyMaster, on_delete=models.CASCADE)

    level = models.IntegerField()  # 1, 2, 3
    role = models.CharField(max_length=100)  # Manager, Finance, etc

    is_active = models.BooleanField(default=True)
    
class ExpenseApproval(models.Model):
    expense = models.ForeignKey(ExpenseEntry, related_name='approvals', on_delete=models.CASCADE)

    level = models.IntegerField()

    approved_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=20, choices=(
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ), default='pending')

    remarks = models.TextField(blank=True, null=True)

    action_date = models.DateTimeField(null=True, blank=True)
