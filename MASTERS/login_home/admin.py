# Home page admin configuration for managing departments, employees, and manual attendance records in the admin interface of the MASTERS app.
from django.contrib import admin
from .models import Department, Employee, ManualAttendance


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'user', 'department', 'designation', 'is_active', 'created_at']
    list_filter = ['department', 'is_active', 'created_at']
    search_fields = ['employee_id', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User Info', {'fields': ('user', 'employee_id')}),
        ('Employment Details', {'fields': ('department', 'designation', 'date_of_joining', 'phone')}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(ManualAttendance)
class ManualAttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'attendance_date', 'status', 'check_in_time', 'check_out_time', 'recorded_by', 'recorded_at']
    list_filter = ['status', 'attendance_date', 'employee__department']
    search_fields = ['employee__employee_id', 'employee__user__first_name', 'employee__user__last_name']
    readonly_fields = ['recorded_at', 'updated_at', 'recorded_by']
    fieldsets = (
        ('Attendance Info', {'fields': ('employee', 'attendance_date')}),
        ('Status & Time', {'fields': ('status', 'check_in_time', 'check_out_time')}),
        ('Additional Info', {'fields': ('remarks',)}),
        ('Recorded By', {'fields': ('recorded_by',)}),
        ('Timestamps', {'fields': ('recorded_at', 'updated_at')}),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
