from django.db import models


class ESGComplianceRegister(models.Model):

    CATEGORY_CHOICES = [
        ("Environmental", "Environmental"),
        ("Social", "Social"),
        ("Governance", "Governance"),
        ("Safety", "Safety"),
        ("Statutory", "Statutory"),
    ]

    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    ]

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(max_length=50, unique=True)

    compliance_type_name = models.CharField(max_length=255)

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    effective_date = models.DateField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")

    description = models.TextField(null=True, blank=True)

    remarks = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "esg_compliance_register"
        ordering = ["-id"]

    def __str__(self):
        return self.compliance_type_name


class ESGComplianceEntry(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(max_length=50, unique=True)

    company_id = models.CharField(max_length=50)

    project_id = models.CharField(max_length=50)

    compliance_type_id = models.CharField(max_length=50)

    issue_date = models.DateField()

    expiry_date = models.DateField()

    notify_days = models.IntegerField(default=0)

    status = models.CharField(max_length=20, default="Active")

    responsible_person = models.CharField(max_length=100)

    reference_no = models.CharField(max_length=100)

    remarks = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, blank=True, null=True)

    session_id = models.CharField(max_length=50, blank=True, null=True)

    sess_user_type = models.CharField(max_length=50, blank=True, null=True)

    sess_user_id = models.CharField(max_length=50, blank=True, null=True)

    sess_company_id = models.CharField(max_length=50, blank=True, null=True)

    sess_branch_id = models.CharField(max_length=50, blank=True, null=True)
    

    class Meta:
        db_table = "esg_compliance_entry"
        ordering = ["-id"]

    def __str__(self):
        return self.unique_id

class InsuranceRegister(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True
    )

    company_id = models.CharField(max_length=50)

    project_id = models.CharField(max_length=50)

    description = models.TextField(
        blank=True,
        null=True
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    session_id = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    sess_user_type = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    sess_user_id = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    sess_company_id = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    sess_branch_id = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    class Meta:
        db_table = "insurance_register"

class InsuranceRegisterDetail(models.Model):

    register = models.ForeignKey(
        InsuranceRegister,
        on_delete=models.CASCADE,
        related_name="details"
    )

    policy_asset = models.CharField(
        max_length=200
    )

    policy_no = models.CharField(
        max_length=100
    )

    issue_date = models.DateField()

    validity = models.DateField()

    notify_days = models.IntegerField(
        default=0
    )

    status = models.CharField(
        max_length=20,
        default="Active"
    )

    insurer = models.CharField(
        max_length=200
    )

    coverage = models.CharField(
        max_length=200
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    last_notified_on = models.DateField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = "insurance_register_details"
class ESGComplianceHistory(models.Model):

    STATUS_CHOICES = [
        ("active", "Active"),
        ("renewal_due", "Renewal Due"),
        ("expired", "Expired"),
        ("closed", "Closed"),
    ]

    id = models.AutoField(primary_key=True)

    compliance_entry = models.ForeignKey(
        ESGComplianceEntry,
        on_delete=models.CASCADE,
        related_name="history"
    )

    issue_date = models.DateField()

    expiry_date = models.DateField()

    notify_days = models.IntegerField(default=30)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="active"
    )

    responsible_person = models.CharField(
        max_length=100
    )

    reference_no = models.CharField(
        max_length=100
    )

    document = models.FileField(
        upload_to="compliance_documents/",
        null=True,
        blank=True
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    last_notified_on = models.DateField(
        null=True,
        blank=True
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    updated = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "esg_compliance_history"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.compliance_entry.unique_id}"


class ESGComplianceStateLog(models.Model):

    id = models.AutoField(primary_key=True)

    compliance_history = models.ForeignKey(
        ESGComplianceHistory,
        on_delete=models.CASCADE,
        related_name="state_logs"
    )

    from_status = models.CharField(
        max_length=30
    )

    to_status = models.CharField(
        max_length=30
    )

    transition_date = models.DateField(
        auto_now_add=True
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "esg_compliance_state_log"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.from_status} -> {self.to_status}"

class ESGComplianceMailLog(models.Model):

    id = models.AutoField(primary_key=True)

    compliance_history = models.ForeignKey(
        ESGComplianceHistory,
        on_delete=models.CASCADE,
        related_name="mail_logs"
    )

    email_type = models.CharField(
        max_length=30
    )

    sent_to = models.TextField()

    sent_on = models.DateTimeField(
        auto_now_add=True
    )

    subject = models.CharField(
        max_length=500
    )

    class Meta:
        db_table = "esg_compliance_mail_log"
        ordering = ["-id"]

    def __str__(self):
        return self.subject
