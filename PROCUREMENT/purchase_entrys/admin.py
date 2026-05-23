"""Admin registrations for procurement entry masters and transactions."""

from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderApproval, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "contact_no", "is_active")
    search_fields = ("name", "contact_person", "contact_no")
    list_filter = ("is_active",)


class PurchaseOrderApprovalInline(admin.TabularInline):
    model = PurchaseOrderApproval
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        "po_number",
        "company",
        "project",
        "supplier",
        "entry_date",
        "gross_amount",
        "workflow_status",
    )
    search_fields = ("po_number", "supplier__name", "project__name")
    list_filter = ("workflow_status", "entry_date")
    readonly_fields = ("items_data",)
    inlines = [PurchaseOrderApprovalInline]
