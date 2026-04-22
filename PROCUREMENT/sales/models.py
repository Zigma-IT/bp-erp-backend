import uuid

from decimal import Decimal

from django.db import models
from django.utils import timezone

from common_master.models import Company as CompanyMaster
from common_master.models import Project as ProjectMaster
from purchase_master.models import ProductCreation as ProductMaster
from purchase_master.models import ItemGroup
from purchase_master.models import SubGroup
from purchase_master.models import UnitMaster
from purchase_entrys.models import Supplier


class UniqueIDMixin(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        abstract = True


# Sales order
class Customer(UniqueIDMixin):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class SalesOrder(UniqueIDMixin):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    entry_date = models.DateField()

    company = models.ForeignKey(CompanyMaster, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    so_number = models.CharField(max_length=100, unique=True, blank=True)

    so_type = models.CharField(max_length=100)
    currency = models.CharField(max_length=50)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, default= Decimal ("1.00"))

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


class SalesOrderItem(UniqueIDMixin):
    sales_order = models.ForeignKey(SalesOrder, related_name='items', on_delete=models.CASCADE)

    product = models.ForeignKey(
        ProductMaster,
        on_delete=models.PROTECT,
        related_name='sales_order_items',
        null=True,
        blank=True,
    )
    unit = models.ForeignKey(
        UnitMaster,
        on_delete=models.PROTECT,
        related_name='sales_order_items',
        null=True,
        blank=True,
    )
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default= Decimal ("1.00"))

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    sub_task = models.CharField(max_length=255, blank=True, null=True)

    class Meta(UniqueIDMixin.Meta):
        ordering = ['id']

    def __str__(self):
        product_name = self.product.product_name if self.product else f"Item-{self.pk}"
        return f"{self.sales_order} - {product_name}"


# Sales Invoice
class SalesInvoice(UniqueIDMixin):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    invoice_date = models.DateField()
    payment_due_date = models.DateField(blank=True, null=True)

    company = models.ForeignKey(CompanyMaster, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    invoice_number = models.CharField(max_length=100, unique=True, blank=True)

    remarks = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(UniqueIDMixin.Meta):
        ordering = ['-invoice_date', '-id']

    def __str__(self):
        return self.invoice_number or f"INV-{self.pk}"

    def generate_invoice_number(self):
        invoice_date = self.invoice_date or timezone.localdate()
        fy_start = invoice_date.year if invoice_date.month >= 4 else invoice_date.year - 1
        fy_end = fy_start + 1
        company_code = (self.company.code or "GEN").upper()
        prefix = f"INV/{fy_start}-{fy_end}/{company_code}"

        last_invoice_number = (
            SalesInvoice.objects.filter(invoice_number__startswith=prefix)
            .order_by('-id')
            .values_list('invoice_number', flat=True)
            .first()
        )

        next_number = 1
        if last_invoice_number:
            try:
                next_number = int(last_invoice_number.rsplit('/', 1)[1]) + 1
            except (IndexError, ValueError):
                next_number = SalesInvoice.objects.filter(
                    invoice_number__startswith=prefix
                ).count() + 1

        return f"{prefix}/{next_number:03d}"

    def save(self, *args, **kwargs):
        try:
            company = self.company
        except CompanyMaster.DoesNotExist:
            company = None
        if not self.invoice_number and company and company.pk is not None:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)


class SalesInvoiceItem(UniqueIDMixin):
    sales_invoice = models.ForeignKey(SalesInvoice, related_name='items', on_delete=models.CASCADE)

    product = models.ForeignKey(
        ProductMaster,
        on_delete=models.PROTECT,
        related_name='sales_invoice_items',
        null=True,
        blank=True,
    )
    unit = models.ForeignKey(
        UnitMaster,
        on_delete=models.PROTECT,
        related_name='sales_invoice_items',
        null=True,
        blank=True,
    )
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    discount_type = models.CharField(max_length=50, blank=True, null=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    remarks = models.CharField(max_length=255, blank=True, null=True)

    class Meta(UniqueIDMixin.Meta):
        ordering = ['id']

    def __str__(self):
        product_name = self.product.product_name if self.product else f"Item-{self.pk}"
        return f"{self.sales_invoice} - {product_name}"


class PurchaseExpense(UniqueIDMixin):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    PAYMENT_TYPE_CHOICES = (
        ("cash", "Cash"),
        ("credit", "Credit"),
        ("bank", "Bank"),
    )

    expense_date = models.DateField()
    company = models.ForeignKey(CompanyMaster, on_delete=models.CASCADE)
    project = models.ForeignKey(
        ProjectMaster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    supplier_manual_entry = models.BooleanField(default=False)
    manual_supplier_name = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(
        ItemGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    sub_category = models.ForeignKey(
        SubGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    expense_number = models.CharField(max_length=100, unique=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(UniqueIDMixin.Meta):
        ordering = ["-expense_date", "-id"]

    def __str__(self):
        return self.expense_number or f"EXP-{self.pk}"

    def generate_expense_number(self):
        expense_date = self.expense_date or timezone.localdate()
        fy_start = expense_date.year if expense_date.month >= 4 else expense_date.year - 1
        fy_end = fy_start + 1
        company_code = (self.company.code or "GEN").upper()
        prefix = f"EXP/{fy_start}-{fy_end}/{company_code}"

        last_expense_number = (
            PurchaseExpense.objects.filter(expense_number__startswith=prefix)
            .order_by("-id")
            .values_list("expense_number", flat=True)
            .first()
        )

        next_number = 1
        if last_expense_number:
            try:
                next_number = int(last_expense_number.rsplit("/", 1)[1]) + 1
            except (IndexError, ValueError):
                next_number = PurchaseExpense.objects.filter(
                    expense_number__startswith=prefix
                ).count() + 1

        return f"{prefix}/{next_number:03d}"

    def save(self, *args, **kwargs):
        try:
            company = self.company
        except CompanyMaster.DoesNotExist:
            company = None
        if not self.expense_number and company and company.pk is not None:
            self.expense_number = self.generate_expense_number()
        super().save(*args, **kwargs)


class PurchaseExpenseItem(UniqueIDMixin):
    purchase_expense = models.ForeignKey(
        PurchaseExpense,
        related_name="items",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        ProductMaster,
        on_delete=models.PROTECT,
        related_name="purchase_expense_items",
        null=True,
        blank=True,
    )
    unit = models.ForeignKey(
        UnitMaster,
        on_delete=models.PROTECT,
        related_name="purchase_expense_items",
        null=True,
        blank=True,
    )
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    discount_type = models.CharField(max_length=50, blank=True, null=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    class Meta(UniqueIDMixin.Meta):
        ordering = ["id"]

    def __str__(self):
        product_name = self.product.product_name if self.product else f"Item-{self.pk}"
        return f"{self.purchase_expense} - {product_name}"
