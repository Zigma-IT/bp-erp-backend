from django.db import models


class ShiftCreation(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True
    )

    shift_name = models.CharField(
        max_length=100
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    shift_duration = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    is_delete = models.BooleanField(
        default=False
    )

    updated = models.DateTimeField(
        auto_now=True
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    acc_year = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    session_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    sess_user_type = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_user_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_company_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_branch_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "shift_creation"

    def __str__(self):
        return self.shift_name

class ShiftRoster(models.Model):
    id = models.BigAutoField(primary_key=True)

    main_unique_id = models.CharField(max_length=50)
    project_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    project_name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    employee_id = models.CharField(max_length=50)
    shift_date = models.DateField()

    shift_unique_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    shift_name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    is_weekoff = models.BooleanField(default=False)

    is_holiday = models.BooleanField(default=False)

    is_delete = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    session_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    sess_user_type = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_user_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_company_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_branch_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "shift_roster_details"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.employee_id} - {self.shift_date}"


class WeekoffCreation(models.Model):
    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(max_length=50, unique=True)

    company_id = models.CharField(max_length=355)

    project_id = models.CharField(max_length=355)

    weekoff_days = models.CharField(max_length=100)

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    updated = models.DateTimeField(
        null=True,
        blank=True
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    acc_year = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    session_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_user_type = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_user_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_company_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_branch_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "weekoff_creation"
        ordering = ["-id"]

    def __str__(self):
        return self.unique_id


class HolidayCreation(models.Model):
    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True
    )

    holiday_date = models.DateField()

    holiday_day = models.CharField(
        max_length=15,
        null=True,
        blank=True
    )

    company_id = models.TextField()

    project_id = models.TextField(
        null=True,
        blank=True
    )

    type = models.CharField(max_length=20)

    description = models.CharField(max_length=200)

    is_flexi_leave = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    updated = models.DateTimeField(
        null=True,
        blank=True
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    acc_year = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    session_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_user_type = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_user_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_company_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_branch_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "holiday_creation"
        ordering = ["-id"]

    def __str__(self):
        return self.unique_id

   
class LeaveEntry(models.Model):
    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(max_length=50, unique=True)

    employee_id = models.CharField(max_length=50)

    leave_type_id = models.CharField(max_length=50)

    half_day_avail = models.BooleanField(
        null=True,
        blank=True
    )

    from_date = models.DateField()

    to_date = models.DateField()

    period = models.IntegerField()

    holiday_unique_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    total_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00
    )

    half_day = models.BooleanField(default=False)

    reason = models.TextField(
        null=True,
        blank=True
    )

    status = models.IntegerField(default=0)

    approved_by = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_user_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    created = models.DateTimeField(
        null=True,
        blank=True
    )

    updated_user_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    updated = models.DateTimeField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    acc_year = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    session_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_user_type = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_user_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_company_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    sess_branch_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    reminder_mail_sent_at = models.DateTimeField(
        null=True,
        blank=True
    )

    from_time = models.TimeField(
        null=True,
        blank=True
    )

    to_time = models.TimeField(
        null=True,
        blank=True
    )

    short_type = models.IntegerField(
        default=0
    )  # 1=Forenoon, 2=Afternoon

    class Meta:
        db_table = "leave_entry"
        ordering = ["-id"]

    def __str__(self):
        return self.unique_id