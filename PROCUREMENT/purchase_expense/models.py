"""Database models for purchase expense transactions."""

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from common_master.models import Company as CompanyMaster
from common_master.models import Project as ProjectMaster
from purchase_entrys.models import Supplier


class UniqueIDMixin(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        abstract = True


class PurchaseExpense(UniqueIDMixin):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    expense_number = models.CharField(max_length=100, unique=True, blank=True)

    company = models.ForeignKey(
        CompanyMaster,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="purchase_expenses",
    )
    project = models.ForeignKey(
        ProjectMaster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_constraint=False,
        related_name="purchase_expenses",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_expenses",
    )
    supplier_manual_entry = models.BooleanField(default=False)
    manual_supplier_name = models.CharField(max_length=255, blank=True, null=True)

    # Category snapshot — IDs from masters_db1; names stored for display
    expense_category_id = models.IntegerField(null=True, blank=True)
    expense_category_name = models.CharField(max_length=255, blank=True, null=True)
    expense_sub_category_id = models.IntegerField(null=True, blank=True)
    expense_sub_category_name = models.CharField(max_length=255, blank=True, null=True)
    payment_type_id = models.IntegerField(null=True, blank=True)
    payment_type_name = models.CharField(max_length=255, blank=True, null=True)

    from_company = models.BooleanField(default=False)
    expense_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    level2_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Line items stored as JSON (consistent with purchase_entrys pattern)
    items_data = models.JSONField(default=list, blank=True)

    # Computed header totals
    basic_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_gst = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    round_off = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(UniqueIDMixin.Meta):
        db_table = "purchase_expense"
        ordering = ["-expense_date", "-id"]

    def __str__(self):
        return self.expense_number or f"EXP-{self.pk}"

    def generate_expense_number(self):
        expense_date = self.expense_date or timezone.localdate()
        fy_start = expense_date.year if expense_date.month >= 4 else expense_date.year - 1
        fy_end = fy_start + 1
        company_code = (self.company.code or "GEN").upper()
        prefix = f"EXP/{fy_start}-{fy_end}/{company_code}"

        last = (
            PurchaseExpense.objects.filter(expense_number__startswith=prefix)
            .order_by("-id")
            .values_list("expense_number", flat=True)
            .first()
        )

        next_number = 1
        if last:
            try:
                next_number = int(last.rsplit("/", 1)[1]) + 1
            except (IndexError, ValueError):
                next_number = (
                    PurchaseExpense.objects.filter(expense_number__startswith=prefix).count() + 1
                )

        return f"{prefix}/{next_number:03d}"

    def save(self, *args, **kwargs):
        try:
            company = self.company
        except CompanyMaster.DoesNotExist:
            company = None
        if not self.expense_number and company and company.pk is not None:
            self.expense_number = self.generate_expense_number()
        super().save(*args, **kwargs)
