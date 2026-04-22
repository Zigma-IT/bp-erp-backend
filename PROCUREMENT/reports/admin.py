"""Admin registrations for stored report snapshots."""

from django.contrib import admin

from .models import (
    CompleteGRNReport,
    CompletePRReport,
    CompleteSRNReport,
    POReport,
    PendingGRNReport,
    PendingPRReport,
    PendingSRNReport,
)


class ReportSnapshotAdmin(admin.ModelAdmin):
    readonly_fields = ("unique_id", "filter_signature", "filter_params", "generated_at")
    list_filter = ("generated_at",)
    search_fields = ("filter_signature",)


@admin.register(PendingPRReport)
class PendingPRReportAdmin(ReportSnapshotAdmin):
    list_display = ("pr_no", "company", "project", "item_name", "generated_at")
    search_fields = ReportSnapshotAdmin.search_fields + ("pr_no", "company", "project", "item_name")


@admin.register(CompletePRReport)
class CompletePRReportAdmin(ReportSnapshotAdmin):
    list_display = ("pr_no", "unit", "project_code", "doc_status", "item_status", "generated_at")
    search_fields = ReportSnapshotAdmin.search_fields + ("pr_no", "unit", "project_code", "item_name")


@admin.register(POReport)
class POReportAdmin(ReportSnapshotAdmin):
    list_display = ("po_no", "unit", "project_code", "vendor_name", "total_value", "generated_at")
    search_fields = ReportSnapshotAdmin.search_fields + ("po_no", "unit", "project_code", "vendor_name")


@admin.register(PendingGRNReport)
class PendingGRNReportAdmin(ReportSnapshotAdmin):
    list_display = ("po_no", "company", "project_code", "item_name", "pending_qty", "generated_at")
    search_fields = ReportSnapshotAdmin.search_fields + ("po_no", "company", "project_code", "item_name")


@admin.register(CompleteGRNReport)
class CompleteGRNReportAdmin(ReportSnapshotAdmin):
    list_display = ("grn_no", "company", "project", "item_name", "total_value", "generated_at")
    search_fields = ReportSnapshotAdmin.search_fields + ("grn_no", "company", "project", "item_name")


@admin.register(PendingSRNReport)
class PendingSRNReportAdmin(ReportSnapshotAdmin):
    list_display = ("po_no", "company", "project_code", "item_name", "pending_qty", "generated_at")
    search_fields = ReportSnapshotAdmin.search_fields + ("po_no", "company", "project_code", "item_name")


@admin.register(CompleteSRNReport)
class CompleteSRNReportAdmin(ReportSnapshotAdmin):
    list_display = ("srn_no", "unit", "project", "vendor_name", "generated_at")
    search_fields = ReportSnapshotAdmin.search_fields + ("srn_no", "unit", "project", "vendor_name")
