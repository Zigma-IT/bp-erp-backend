from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    gst_no = models.CharField(max_length=20, blank=True, null=True)
    pan_no = models.CharField(max_length=20, blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    contact_no = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    PO_STATUS = (
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    po_number = models.CharField(max_length=100, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    entry_date = models.DateField()
    quotation_no = models.CharField(max_length=100, blank=True, null=True)
    quotation_date = models.DateField(blank=True, null=True)

    revision_no = models.CharField(max_length=50, default="REV001")
    revision_date = models.DateField(blank=True, null=True)
    revision_remarks = models.TextField(blank=True, null=True)

    total_basic_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    freight_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    packing_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    round_off = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    total_gst = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=PO_STATUS, default='draft')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.po_number


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, related_name='items', on_delete=models.CASCADE)

    product_name = models.CharField(max_length=255)
    uom = models.CharField(max_length=50)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    delivery_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)


# Purchase order approvel level 1
from django.db import models
from .models import PurchaseOrder


class POApprovalLevel1(models.Model):
    po = models.OneToOneField(PurchaseOrder, on_delete=models.CASCADE, related_name='level1')

    approved_net_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_gross_amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(max_length=20, default='pending')
    approved_at = models.DateTimeField(auto_now_add=True)


# Purchase order approvel level 2
class POApprovalLevel2(models.Model):
    po = models.OneToOneField(PurchaseOrder, on_delete=models.CASCADE, related_name='level2')

    approved_net_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_gross_amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(max_length=20, default='pending')
    approved_at = models.DateTimeField(auto_now_add=True)