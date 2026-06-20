"""Database models for purchase master setup screens."""

import uuid

from decimal import Decimal
from typing import cast

from django.db import models


class UniqueIDMixin(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        abstract = True


class UnitMaster(UniqueIDMixin):
    unit_name = models.CharField(max_length=50)
    decimal_points = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "purchase_master_unitmaster"
        ordering = ["-id"]

    def __str__(self):
        return self.unit_name


class ItemGroup(UniqueIDMixin):
    group_name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.group_name} ({self.code})"


class SubGroup(UniqueIDMixin):
    group = models.ForeignKey(ItemGroup, on_delete=models.CASCADE, related_name="sub_groups")
    sub_group_name = models.CharField(max_length=100)
    sub_group_code = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(UniqueIDMixin.Meta):
        abstract = False
        unique_together = ("group", "sub_group_name")

    def __str__(self):
        return f"{self.sub_group_name} ({self.sub_group_code})"


class ProductGroup(UniqueIDMixin):
    group_name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    created_in_product_creation = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["group_name"]

    def __str__(self):
        return f"{self.group_name} ({self.code})"


class ProductSubGroup(UniqueIDMixin):
    group = models.ForeignKey(ProductGroup, on_delete=models.CASCADE, related_name="sub_groups")
    sub_group_name = models.CharField(max_length=100)
    sub_group_code = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    created_in_product_creation = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(UniqueIDMixin.Meta):
        abstract = False
        ordering = ["sub_group_name"]
        unique_together = ("group", "sub_group_name")

    def __str__(self):
        return f"{self.sub_group_name} ({self.sub_group_code})"


# Dedicated, completely isolated tables for Product Creation.
# These have NO foreign key to any master table (ItemGroup, SubGroup, ProductGroup, etc.).
class ProductCreationGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_creation_group"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductCreationSubGroup(models.Model):
    group = models.ForeignKey(
        ProductCreationGroup, on_delete=models.CASCADE, related_name="sub_groups"
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_creation_subgroup"
        ordering = ["name"]
        unique_together = ("group", "name")

    def __str__(self):
        return self.name


class Category(UniqueIDMixin):
    group = models.ForeignKey(ItemGroup, on_delete=models.CASCADE, related_name="categories")
    sub_group = models.ForeignKey(SubGroup, on_delete=models.CASCADE, related_name="categories")
    category_name = models.CharField(max_length=100)
    category_code = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(UniqueIDMixin.Meta):
        abstract = False
        unique_together = ("sub_group", "category_name")

    def __str__(self):
        return f"{self.category_name} ({self.category_code})"


class ItemMaster(UniqueIDMixin):
    group = models.ForeignKey(ItemGroup, on_delete=models.CASCADE)
    sub_group = models.ForeignKey(SubGroup, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    unit = models.ForeignKey(UnitMaster, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=255)
    item_code = models.CharField(max_length=100, unique=True)
    reorder_level = models.IntegerField(default=0)
    reorder_qty = models.IntegerField(default=0)
    purchase_lead_time = models.IntegerField(default=0)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=cast(Decimal, 0),
    )
    hsn_code = models.CharField(max_length=50, blank=True, null=True)
    tolerance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=cast(Decimal, 0),
    )
    tax = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=cast(Decimal, 0),
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.item_name

    class Meta:
        unique_together = ("group", "sub_group", "category", "item_name")
        ordering = ["item_code"]


class ProductCreation(UniqueIDMixin):
    company = models.ForeignKey("common_master.Company", on_delete=models.CASCADE)
    product_group = models.ForeignKey(
        ProductCreationGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    product_sub_group = models.ForeignKey(
        ProductCreationSubGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    product_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product_name


class StandardBOM(UniqueIDMixin):
    product = models.ForeignKey(ProductCreation, on_delete=models.CASCADE, null=True, blank=True)
    semi_finished = models.ForeignKey(ItemMaster, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.product_id and self.product:
            return f"BOM - {self.product.product_name}"
        if self.semi_finished_id and self.semi_finished:
            return f"BOM - {self.semi_finished.item_name}"
        return f"BOM - {self.pk}"


class StandardBOMItem(UniqueIDMixin):
    bom = models.ForeignKey(StandardBOM, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(ItemMaster, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50)
    remarks = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        bom_pk = self.bom.pk if self.bom else None
        return f"{bom_pk} - {self.item.item_name}"


class ExpenseCategory(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True
    )

    category_name = models.CharField(
        max_length=100
    )

    description = models.TextField()

    is_active = models.IntegerField(
        default=1
    )

    is_delete = models.IntegerField(
        default=0
    )

    updated_user_id = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    updated = models.DateTimeField(
        null=True,
        blank=True
    )

    created_user_id = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    acc_year = models.CharField(
        max_length=50
    )

    session_id = models.CharField(
        max_length=50
    )

    sess_user_type = models.CharField(
        max_length=50
    )

    sess_user_id = models.CharField(
        max_length=50
    )

    sess_company_id = models.CharField(
        max_length=50
    )

    sess_branch_id = models.CharField(
        max_length=50
    )

    class Meta:
        db_table = "expense_category"

    def __str__(self):
        return self.category_name


class ExpenseSubCategory(models.Model):
    id = models.AutoField(primary_key=True)
    unique_id = models.CharField(max_length=50, unique=True)

    category_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    sub_category_name = models.CharField(max_length=100)

    description = models.TextField()

    is_active = models.IntegerField(default=1)
    is_delete = models.IntegerField(default=0)

    updated_user_id = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    updated = models.DateTimeField(
        null=True,
        blank=True
    )

    created_user_id = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    created = models.DateTimeField(
        null=True,
        blank=True
    )

    acc_year = models.CharField(max_length=50)

    session_id = models.CharField(max_length=50)

    sess_user_type = models.CharField(max_length=50)

    sess_user_id = models.CharField(max_length=50)

    sess_company_id = models.CharField(max_length=50)

    sess_branch_id = models.CharField(max_length=50)

    class Meta:
        db_table = "expense_sub_category"

    def __str__(self):
        return self.sub_category_name


class CustomerCategory(models.Model):
    customer_category_id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True
    )

    customer_category = models.CharField(
        max_length=150
    )

    description = models.TextField()

    is_active = models.IntegerField(default=1)

    is_delete = models.IntegerField(default=0)

    updated = models.DateTimeField(
        auto_now=True
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    acc_year = models.CharField(
        max_length=50
    )

    session_id = models.CharField(
        max_length=50
    )

    sess_user_type = models.CharField(
        max_length=50
    )

    sess_user_id = models.CharField(
        max_length=50
    )

    sess_company_id = models.CharField(
        max_length=50
    )

    sess_branch_id = models.CharField(
        max_length=50
    )

    class Meta:
        db_table = "customer_category"

    def __str__(self):
        return self.customer_category

class PaymentCategory(models.Model):
    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True
    )

    payment_name = models.CharField(
        max_length=100
    )

    description = models.TextField()

    is_active = models.IntegerField(default=1)

    is_delete = models.IntegerField(default=0)

    updated_user_id = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    updated = models.DateTimeField(
        null=True,
        blank=True
    )

    created_user_id = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    created = models.DateTimeField(
        null=True,
        blank=True
    )

    acc_year = models.CharField(
        max_length=50
    )

    session_id = models.CharField(
        max_length=50
    )

    sess_user_type = models.CharField(
        max_length=50
    )

    sess_user_id = models.CharField(
        max_length=50
    )

    sess_company_id = models.CharField(
        max_length=50
    )

    sess_branch_id = models.CharField(
        max_length=50
    )

    class Meta:
        db_table = "payment_type"

    def __str__(self):
        return self.payment_name