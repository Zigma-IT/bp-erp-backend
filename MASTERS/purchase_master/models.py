from django.db import models


class UnitMaster(models.Model):
    unit_name = models.CharField(max_length=50, unique=True)
    decimal_points = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.unit_name


class ItemGroup(models.Model):
    group_name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.group_name} ({self.code})"


class SubGroup(models.Model):
    group = models.ForeignKey(ItemGroup, on_delete=models.CASCADE, related_name="sub_groups")
    sub_group_name = models.CharField(max_length=100)
    sub_group_code = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("group", "sub_group_name")

    def __str__(self):
        return f"{self.sub_group_name} ({self.sub_group_code})"


class Category(models.Model):
    group = models.ForeignKey(ItemGroup, on_delete=models.CASCADE, related_name="categories")
    sub_group = models.ForeignKey(SubGroup, on_delete=models.CASCADE, related_name="categories")
    category_name = models.CharField(max_length=100)
    category_code = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("sub_group", "category_name")

    def __str__(self):
        return f"{self.category_name} ({self.category_code})"


class ItemMaster(models.Model):
    group = models.ForeignKey(ItemGroup, on_delete=models.CASCADE)
    sub_group = models.ForeignKey(SubGroup, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    unit = models.ForeignKey(UnitMaster, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=255)
    item_code = models.CharField(max_length=100, unique=True)
    reorder_level = models.IntegerField(default=0)
    reorder_qty = models.IntegerField(default=0)
    purchase_lead_time = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hsn_code = models.CharField(max_length=50, blank=True, null=True)
    tolerance = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.item_name


class Company(models.Model):
    company_name = models.CharField(max_length=150)

    def __str__(self):
        return self.company_name


class ProductCreation(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    group = models.ForeignKey(ItemGroup, on_delete=models.SET_NULL, null=True, blank=True)
    sub_group = models.ForeignKey(SubGroup, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product_name


class StandardBOM(models.Model):
    product = models.ForeignKey(ProductCreation, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BOM - {self.product.product_name}"


class StandardBOMItem(models.Model):
    bom = models.ForeignKey(StandardBOM, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(ItemMaster, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50)
    remarks = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.bom_id} - {self.item.item_name}"
