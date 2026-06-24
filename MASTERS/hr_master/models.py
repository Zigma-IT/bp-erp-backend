import uuid
from django.db import models


class DepartmentCreation(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    department = models.CharField(max_length=255)

    department_head = models.CharField(max_length=255)

    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    )

    active_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active'
    )

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    

    class Meta:
        db_table = "department_creation"
        ordering = ['-id']

    def __str__(self):
        return self.department



class DesignationCreation(models.Model):

    STRUCTURE_CHOICES = (
        ('Grade Based', 'Grade Based'),
        ('Band Based', 'Band Based'),
    )

    unique_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    structure_type = models.CharField(
        max_length=50,
        choices=STRUCTURE_CHOICES,
        default='Grade Based'
    )

    grade_type = models.CharField(max_length=255, blank=True, default='')

    band = models.ForeignKey(
        'BandMaster',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='band_id',
        related_name='designations'
    )

    level = models.ForeignKey(
        'LevelMaster',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='level_id',
        related_name='designations'
    )

    designation = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "designation_creation"
        ordering = ['-id']

    def __str__(self):
        return self.designation


class StaffCreation(models.Model):

    staff_id = models.AutoField(primary_key=True)

    unique_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    # PERSONAL DETAILS
    staff_name = models.CharField(max_length=255)
    father_name = models.CharField(max_length=255, null=True, blank=True)
    employee_id = models.CharField(max_length=255, null=True, blank=True)

    premises_type = models.CharField(max_length=255, null=True, blank=True)

    branch_id = models.CharField(max_length=255, null=True, blank=True)

    attendance_setting_id = models.CharField(max_length=255, null=True, blank=True)

    doc_dob = models.DateField(null=True, blank=True)

    date_of_birth = models.DateField(null=True, blank=True)

    personal_contact_no = models.CharField(max_length=20)

    age = models.IntegerField(null=True, blank=True)

    qualification = models.CharField(max_length=255, null=True, blank=True)

    graduation_type = models.CharField(max_length=255, null=True, blank=True)

    gender = models.CharField(max_length=50)

    martial_status = models.CharField(max_length=50, null=True, blank=True)

    office_contact_no = models.CharField(max_length=20, null=True, blank=True)

    personal_email_id = models.EmailField(null=True, blank=True)

    office_email_id = models.EmailField(null=True, blank=True)

    blood_group = models.CharField(max_length=20, null=True, blank=True)

    aadhar_no = models.CharField(max_length=30, null=True, blank=True)

    license_no = models.CharField(max_length=255, null=True, blank=True)

    pan_no = models.CharField(max_length=30, null=True, blank=True)

    gst_no = models.CharField(max_length=50, null=True, blank=True)

    claim_status = models.CharField(max_length=50, null=True, blank=True)

    # PRESENT ADDRESS
    pre_country = models.CharField(max_length=255, null=True, blank=True)
    pre_state = models.CharField(max_length=255, null=True, blank=True)
    pre_city = models.CharField(max_length=255, null=True, blank=True)
    pre_building_no = models.CharField(max_length=255, null=True, blank=True)
    pre_street = models.CharField(max_length=255, null=True, blank=True)
    pre_area = models.CharField(max_length=255, null=True, blank=True)
    pre_pincode = models.CharField(max_length=20, null=True, blank=True)

    # PERMANENT ADDRESS
    same_address_status = models.BooleanField(default=False)

    perm_country = models.CharField(max_length=255, null=True, blank=True)
    perm_state = models.CharField(max_length=255, null=True, blank=True)
    perm_city = models.CharField(max_length=255, null=True, blank=True)
    perm_building_no = models.CharField(max_length=255, null=True, blank=True)
    perm_street = models.CharField(max_length=255, null=True, blank=True)
    perm_area = models.CharField(max_length=255, null=True, blank=True)
    perm_pincode = models.CharField(max_length=20, null=True, blank=True)

    # OFFICE DETAILS
    date_of_join = models.DateField(null=True, blank=True)

    grade = models.CharField(max_length=255, null=True, blank=True)

    designation_unique_id = models.CharField(max_length=255, null=True, blank=True)

    work_location = models.CharField(max_length=255, null=True, blank=True)

    department = models.CharField(max_length=255, null=True, blank=True)

    biometric_id = models.CharField(max_length=255, null=True, blank=True)

    salary_category = models.CharField(max_length=255, null=True, blank=True)

    reporting_officer = models.CharField(max_length=255, null=True, blank=True)

    esi_no = models.CharField(max_length=255, null=True, blank=True)

    pf_no = models.CharField(max_length=255, null=True, blank=True)

    company_name = models.CharField(max_length=255, null=True, blank=True)

    # SALARY DETAILS
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    basic_wages = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_basic_wages = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    hra = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_hra = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    conveyance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_conveyance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    education_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_education_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    other_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_other_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    pf = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_pf = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    esi = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_esi = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    total_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_total_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    purformance_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_purformance_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    ctc = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    annum_ctc = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # STATUS
    status = models.CharField(max_length=100, default="Active")

    relieve_date = models.DateField(null=True, blank=True)

    relieve_status = models.CharField(max_length=100, null=True, blank=True)

    relieve_reason = models.TextField(null=True, blank=True)

    # FILE
    file_name = models.FileField(
        upload_to='staff_files/',
        null=True,
        blank=True
    )

    file_original_name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    updated = models.DateTimeField(auto_now=True)

    created = models.DateTimeField(auto_now_add=True)

    acc_year = models.CharField(max_length=50, null=True, blank=True)

    session_id = models.CharField(max_length=255, null=True, blank=True)

    sess_user_type = models.CharField(max_length=255, null=True, blank=True)

    sess_branch_id = models.CharField(max_length=255, null=True, blank=True)

    sess_company_id = models.CharField(max_length=255, null=True, blank=True)

    sess_user_typer = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "staff_creation"
        ordering = ['-staff_id']

    def __str__(self):
        return self.staff_name



class StaffEmploymentStatus(models.Model):

    staff_employment_status_id = models.AutoField(
        primary_key=True
    )

    unique_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    staff_unique_id = models.CharField(
        max_length=255
    )

    effective_from = models.DateField(
        null=True,
        blank=True
    )

    effective_to = models.DateField(
        null=True,
        blank=True
    )

    conf_due_date = models.DateField(
        null=True,
        blank=True
    )

    conf_date = models.DateField(
        null=True,
        blank=True
    )

    employment_status = models.CharField(
        max_length=255
    )

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    updated = models.DateTimeField(auto_now=True)

    created = models.DateTimeField(auto_now_add=True)

    acc_year = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    session_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    sess_user_type = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    sess_user_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    sess_company_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    sess_branch_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "staff_employment_status"
        ordering = ['-staff_employment_status_id']

    def __str__(self):
        return self.employment_status

        


class StaffDependentDetails(models.Model):

    staff_dep_id = models.AutoField(
        primary_key=True
    )

    unique_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    staff_unique_id = models.CharField(
        max_length=50
    )

    relationship = models.CharField(
        max_length=50
    )

    name = models.CharField(
        max_length=50
    )

    gender = models.CharField(
        max_length=50
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    aadhar_no = models.CharField(
        max_length=50
    )

    occupation = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    standard = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    school = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    existing_illness = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    illness_description = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    
    existing_insurance = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    insurance_no = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    physically_challenged = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    remarks = models.TextField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    updated = models.DateTimeField(auto_now=True)

    created = models.DateTimeField(auto_now_add=True)

    acc_year = models.CharField(
        max_length=50,
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
        db_table = "staff_dependent_details"
        ordering = ['-staff_dep_id']

    def __str__(self):
        return self.name



class StaffAccountDetails(models.Model):

    staff_acc_id = models.AutoField(
        primary_key=True
    )

    unique_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    staff_unique_id = models.CharField(
        max_length=100
    )

    salary_type = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    bank_status = models.CharField(
        max_length=20
    )

    bank_name = models.CharField(
        max_length=100
    )

    account_no = models.CharField(
        max_length=100
    )

    accountant_name = models.CharField(
        max_length=100
    )

    ifsc_code = models.CharField(
        max_length=100
    )

    contact_no = models.CharField(
        max_length=100
    )

    gst_no = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    address = models.TextField()

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    updated = models.DateTimeField(auto_now=True)

    created = models.DateTimeField(auto_now_add=True)

    acc_year = models.CharField(
        max_length=50,
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
        db_table = "staff_account_details"
        ordering = ['-staff_acc_id']

    def __str__(self):
        return self.accountant_name

class StaffQualificationDetails(models.Model):

    staff_qual_id = models.AutoField(primary_key=True)

    unique_id = models.CharField(max_length=50)

    staff_unique_id = models.CharField(max_length=50)

    education_type = models.CharField(max_length=50)

    degree = models.CharField(max_length=50)

    college_name = models.CharField(max_length=100)

    year_passing = models.CharField(max_length=50)

    percentage = models.CharField(max_length=50)

    university = models.CharField(max_length=100)

    doc_name = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.IntegerField(default=1)

    is_delete = models.IntegerField(default=0)

    updated = models.DateTimeField(auto_now=True)

    created = models.DateTimeField(auto_now_add=True)

    acc_year = models.CharField(max_length=50)

    session_id = models.CharField(max_length=50)

    sess_user_type = models.CharField(max_length=50)

    sess_user_id = models.CharField(max_length=50)

    sess_company_id = models.CharField(max_length=50)

    sess_branch_id = models.CharField(max_length=50)

    class Meta:

        db_table = 'staff_qualification_details'

    def __str__(self):

        return self.unique_id


class LwfEntry(models.Model):

    lwf_id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True
    )

    project_id = models.CharField(
        max_length=50
    )

    state = models.CharField(
        max_length=50
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    deduction_frequency = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    deduction_months = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    employer_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    excluded_designations = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    effective_from = models.DateField(
        null=True,
        blank=True
    )

    is_active = models.IntegerField(
        default=1
    )

    is_delete = models.IntegerField(
        default=0
    )

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

        db_table = "lwf_entry"

    def __str__(self):

        return self.unique_id
class ProfessionalTax(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True
    )

    project_id = models.CharField(
        max_length=255
    )

    state = models.CharField(
        max_length=100
    )

    salary_from = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    salary_to = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    gender = models.CharField(
        max_length=20,
        default='All'
    )

    deduction_frequency = models.CharField(
        max_length=50
    )

    period_start_month = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    period_end_month = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    deduction_month = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    special_month = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    annual_cap = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    acc_year = models.CharField(max_length=50)

    session_id = models.CharField(max_length=50)

    sess_user_type = models.CharField(max_length=50)

    sess_user_id = models.CharField(max_length=50)

    sess_company_id = models.CharField(max_length=50)

    sess_branch_id = models.CharField(max_length=50)

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)

    is_salary_slab = models.BooleanField(default=False)

    is_gender_bound = models.BooleanField(default=False)

    is_special_month = models.BooleanField(default=False)

    is_annual_cap = models.BooleanField(default=False)

    special_amt = models.IntegerField(
        null=True,
        blank=True
    )

    class Meta:

        db_table = "prof_tax"

    def __str__(self):

        return self.unique_id

class LeaveMasterCreation(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(max_length=50)

    leave_type = models.CharField(max_length=100)

    policy_unique_id = models.CharField(
        max_length=30,
        null=True,
        blank=True
    )

    annual_entitlement = models.BooleanField(default=False)

    balance_handling = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    max_carry_forward = models.IntegerField(default=0)

    accrual_method = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    accrual_monthly_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    gender_applicable = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    min_service_months = models.IntegerField(default=0)

    max_occurrences_per_year = models.IntegerField(default=0)

    half_day = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    children_limit = models.IntegerField(default=0)

    is_document_required = models.BooleanField(default=False)

    document_text = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    is_sandwich_applicable = models.BooleanField(default=False)

    excess_handling = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    notice_period_days = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    updated = models.DateTimeField(
        auto_now=True,
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

        db_table = "leave_master_creation"

    def __str__(self):

        return self.leave_type

class ReasonCreation(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50
    )

    reason_name = models.CharField(
        max_length=100
    )

    description = models.TextField()

    is_active = models.BooleanField(
        default=True
    )

    is_delete = models.BooleanField(
        default=False
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
        max_length=50,
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
        db_table = "reason_creation"

    def __str__(self):
        return self.reason_name


class PayCycle(models.Model):

    id = models.AutoField(primary_key=True)

    name = models.CharField(
        max_length=100,
        unique=True
    )

    from_day = models.PositiveSmallIntegerField()

    to_day = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    last_day_flag = models.BooleanField(
        default=False
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    created_by = models.IntegerField(
        null=True,
        blank=True
    )

    updated_by = models.IntegerField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = "pay_cycle"

    def __str__(self):
        return self.name


class SalaryCategory(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True
    )

    salary_category = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True,
        null=True
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
        db_table = "salary_category"

    def __str__(self):
        return self.salary_category

class GradeMaster(models.Model):

    id = models.AutoField(primary_key=True)

    grade_name = models.CharField(max_length=100)

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    updated = models.DateTimeField(auto_now=True)

    created = models.DateTimeField(auto_now_add=True)

    acc_year = models.CharField(max_length=50)

    session_id = models.CharField(max_length=50)

    sess_user_type = models.CharField(max_length=50)

    sess_user_id = models.CharField(max_length=50)

    sess_company_id = models.CharField(max_length=50)

    sess_branch_id = models.CharField(max_length=50)

    class Meta:
        db_table = "grade_master"

    def __str__(self):
        return self.grade_name


class BandMaster(models.Model):

    id = models.AutoField(primary_key=True)

    band_name = models.CharField(
        max_length=50
    )

    is_active = models.BooleanField(
        default=True
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
        db_table = "band_master"

    def __str__(self):
        return self.band_name


class LevelMaster(models.Model):

    id = models.AutoField(primary_key=True)

    band = models.ForeignKey(
        BandMaster,
        on_delete=models.PROTECT,
        db_column="band_id"
    )

    level_name = models.CharField(
        max_length=100
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
        db_table = "level_master"

    def __str__(self):
        return self.level_name