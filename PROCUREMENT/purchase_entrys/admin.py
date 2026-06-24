"""Admin registrations for procurement entry masters and transactions."""

from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderApproval, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("supplier_code", "name", "contact_person", "contact_no", "is_active")
    search_fields = ("supplier_code", "name", "contact_person", "contact_no")
    list_filter = ("is_active",)


class PurchaseOrderApprovalInline(admin.TabularInline):
    model = PurchaseOrderApproval
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        "po_number",
        "company_code",
        "project_code",
        "supplier_code",
        "entry_date",
        "gross_amount",
        "workflow_status",
    )
    search_fields = ("po_number", "supplier_code", "supplier_name", "project_code")
    list_filter = ("workflow_status", "entry_date")
    readonly_fields = ("items_data",)
    inlines = [PurchaseOrderApprovalInline]
