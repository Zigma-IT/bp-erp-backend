"""Database models for shared common masters used across modules."""

import uuid

from django.db import models


def generate_legacy_unique_id():
    return str(uuid.uuid4())


class UniqueIDMixin(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        abstract = True

class Continent(UniqueIDMixin):
    name = models.CharField(max_length=100, unique=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Country(UniqueIDMixin):
    continent = models.ForeignKey(
        Continent,
        on_delete=models.CASCADE,
        related_name="countries",
    )
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=10)
    currency = models.CharField(max_length=50, blank=True, null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(UniqueIDMixin.Meta):
        abstract = False
        unique_together = ("name", "code")
        ordering = ["name"]

    def __str__(self):
        return self.name


class State(UniqueIDMixin):
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="states",
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(UniqueIDMixin.Meta):
        abstract = False
        unique_together = ("country", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


class CommonMaster(UniqueIDMixin):
    type = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta(UniqueIDMixin.Meta):
        abstract = False
        db_table = "common_master"
        ordering = ["type", "name"]

    def __str__(self):
        return self.name

#City
class City(UniqueIDMixin):
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="cities",
    )
    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name="cities",
    )
    name = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    city_type = models.ForeignKey(
        CommonMaster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cities",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(UniqueIDMixin.Meta):
        abstract = False
        db_table = "common_master_city"
        unique_together = ("state", "name")
        indexes = [
            models.Index(fields=["state"]),
            models.Index(fields=["name"]),
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name

# tax 
class Tax(UniqueIDMixin):
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="taxes",
    )
    name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(UniqueIDMixin.Meta):
        abstract = False
        db_table = "common_master_tax"
        unique_together = ("country", "name")
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["country"]),
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name


#Company Creation
class Company(UniqueIDMixin):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)

    pincode = models.CharField(max_length=10, null=True, blank=True)

    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    logo = models.ImageField(upload_to='company/logo/', null=True, blank=True)
    document = models.FileField(upload_to='company/docs/', null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(UniqueIDMixin.Meta):
        abstract = False
        db_table = "common_master_CompanyCreation"
        ordering = ["-id"]

    def __str__(self):
        return self.name
    

# Project Creation
class Project(UniqueIDMixin):
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='projects')

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)

    client_name = models.CharField(max_length=255, null=True, blank=True)

    application_type = models.ForeignKey(
        CommonMaster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'type': 'APPLICATION_TYPE'}
    )

    capacity = models.CharField(max_length=100, null=True, blank=True)
    duration = models.CharField(max_length=100, null=True, blank=True)

    project_date = models.DateField()

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)

    address = models.TextField(null=True, blank=True)

    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    pincode = models.CharField(max_length=10, null=True, blank=True)

    pan_number = models.CharField(max_length=20, null=True, blank=True)
    gst_number = models.CharField(max_length=20, null=True, blank=True)
    gst_reg_date = models.DateField(null=True, blank=True)

    contact_person = models.CharField(max_length=150, null=True, blank=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    contact_email = models.EmailField(null=True, blank=True)

    website = models.URLField(null=True, blank=True)

    description = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta(UniqueIDMixin.Meta):
        abstract = False
        db_table = "common_master_ProjectCreation"
        ordering = ["-id"]

    def __str__(self):
        return self.name
        
class CustomerProfile(UniqueIDMixin):
    unique_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        default=generate_legacy_unique_id,
    )
    
    customer_name = models.CharField(max_length=255)
    customer_no = models.CharField(max_length=100)

    customer_group_id = models.IntegerField(null=True, blank=True)
    customer_sub_category_id = models.IntegerField(null=True, blank=True)
    property = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=50, null=True, blank=True)

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)

    address = models.TextField(null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)

    gst_status = models.BooleanField(default=False)
    gst_no = models.CharField(max_length=50, null=True, blank=True)
    pan_no = models.CharField(max_length=20, null=True, blank=True)

    mobile_no = models.CharField(max_length=15)
    phone_no = models.CharField(max_length=15, null=True, blank=True)
    email_id = models.EmailField(null=True, blank=True)

    provisional_status = models.BooleanField(default=False)
    provisional_no = models.CharField(max_length=50, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acc_year = models.CharField(max_length=20, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "customer_profile"
        managed = False
        ordering = ["-id"]

    def __str__(self):
        return self.customer_name


class CustomerContactPerson(UniqueIDMixin):
    customer = models.ForeignKey(
        'CustomerProfile',
        on_delete=models.CASCADE,
        related_name='contact_persons'
    )

    contact_person_name = models.CharField(max_length=255)
    contact_person_designation = models.CharField(max_length=255, null=True, blank=True)

    contact_person_address1 = models.TextField(null=True, blank=True)
    contact_person_address2 = models.TextField(null=True, blank=True)

    contact_person_email = models.EmailField(null=True, blank=True)
    contact_person_contact_no = models.CharField(max_length=15)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, null=True, blank=True)

    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "customer_contact_person"
        ordering = ["-id"]

    def __str__(self):
        return self.contact_person_name


class CustomerStatutoryDetails(UniqueIDMixin):
    customer = models.ForeignKey(
        'CustomerProfile',
        on_delete=models.CASCADE,
        related_name='statutory_details'
    )

    ecc_no = models.CharField(max_length=100, null=True, blank=True)
    commissionerate = models.CharField(max_length=255, null=True, blank=True)
    division = models.CharField(max_length=255, null=True, blank=True)
    range = models.CharField(max_length=255, null=True, blank=True)

    cst_no = models.CharField(max_length=100, null=True, blank=True)
    trn_no = models.CharField(max_length=100, null=True, blank=True)
    service_tax_no = models.CharField(max_length=100, null=True, blank=True)
    iec_code = models.CharField(max_length=100, null=True, blank=True)

    cin_no = models.CharField(max_length=100, null=True, blank=True)
    tan_no = models.CharField(max_length=100, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, null=True, blank=True)

    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "customer_statutory_details"
        ordering = ["-id"]

    def __str__(self):
        return f"Statutory - {self.customer.customer_name}"


class CustomerAccountDetails(UniqueIDMixin):
    customer = models.ForeignKey(
        'CustomerProfile',
        on_delete=models.CASCADE,
        related_name='account_details'
    )

    bank_name = models.CharField(max_length=255)
    bank_address = models.TextField(null=True, blank=True)

    ifsc_code = models.CharField(max_length=20)
    beneficiary_account_name = models.CharField(max_length=255)
    account_no = models.CharField(max_length=50)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, null=True, blank=True)

    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "customer_account_details"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.bank_name} - {self.account_no}"


class CustomerBillingDetails(UniqueIDMixin):
    customer = models.ForeignKey(
        'CustomerProfile',
        on_delete=models.CASCADE,
        related_name='billing_details'
    )

    name = models.CharField(max_length=255)
    address = models.TextField()

    # ✅ Foreign Keys (master reference)
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True)

    # ✅ Snapshot fields (important)
    country_name = models.CharField(max_length=100, null=True, blank=True)
    state_name = models.CharField(max_length=100, null=True, blank=True)
    city_name = models.CharField(max_length=100, null=True, blank=True)

    contact_name = models.CharField(max_length=255, null=True, blank=True)
    contact_no = models.CharField(max_length=15, null=True, blank=True)

    gst_no = models.CharField(max_length=50, null=True, blank=True)
    gst_status = models.CharField(max_length=20, default="Active")

    ecc_no = models.CharField(max_length=50, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, null=True, blank=True)

    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "customer_billing_details"
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        # ✅ Auto fill snapshot fields
        if self.country:
            self.country_name = self.country.name
        if self.state:
            self.state_name = self.state.name
        if self.city:
            self.city_name = self.city.name

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class CustomerShippingDetails(UniqueIDMixin):
    customer = models.ForeignKey(
        'CustomerProfile',
        on_delete=models.CASCADE,
        related_name='shipping_details'
    )

    name = models.CharField(max_length=255)
    address = models.TextField()

    # FK (master reference)
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True)

    # Snapshot fields
    country_name = models.CharField(max_length=100, null=True, blank=True)
    state_name = models.CharField(max_length=100, null=True, blank=True)
    city_name = models.CharField(max_length=100, null=True, blank=True)

    contact_name = models.CharField(max_length=255, null=True, blank=True)
    contact_no = models.CharField(max_length=15, null=True, blank=True)

    gst_no = models.CharField(max_length=50, null=True, blank=True)
    gst_status = models.CharField(max_length=20, default="Active")

    ecc_no = models.CharField(max_length=50, null=True, blank=True)

    # 🔥 Important field
    is_same_as_billing = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, null=True, blank=True)

    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "customer_shipping_details"
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        # snapshot auto fill
        if self.country:
            self.country_name = self.country.name
        if self.state:
            self.state_name = self.state.name
        if self.city:
            self.city_name = self.city.name

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CustomerDocument(UniqueIDMixin):
    customer = models.ForeignKey(
        'CustomerProfile',
        on_delete=models.CASCADE,
        related_name='documents'
    )

    # document type (like PAN, GST, etc)
    document_type = models.ForeignKey(
        'CommonMaster',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'type': 'DOCUMENT_TYPE'}
    )

    document_name = models.CharField(max_length=255, null=True, blank=True)

    # file upload
    file = models.FileField(upload_to='customer_documents/')

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, null=True, blank=True)

    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "customer_documents"
        ordering = ["-id"]

    def __str__(self):
        return self.document_name or "Document"
class SupplierProfile(UniqueIDMixin):
    vendor_name = models.CharField(max_length=255)
    group = models.ForeignKey(CommonMaster, on_delete=models.SET_NULL, null=True, blank=True)
    currency = models.CharField(max_length=50, null=True, blank=True)
    reference = models.CharField(max_length=255, null=True, blank=True)

    is_manufacturer = models.BooleanField(default=False)
    is_agent_dealer = models.BooleanField(default=False)
    is_service_jobwork = models.BooleanField(default=False)

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)

    country_name = models.CharField(max_length=100, null=True, blank=True)
    state_name = models.CharField(max_length=100, null=True, blank=True)
    city_name = models.CharField(max_length=100, null=True, blank=True)

    pincode = models.CharField(max_length=10, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    corporate_address = models.TextField(null=True, blank=True)
    phone_no = models.CharField(max_length=15, null=True, blank=True)
    fax_no = models.CharField(max_length=15, null=True, blank=True)
    pan_no = models.CharField(max_length=20, null=True, blank=True)
    gst_no = models.CharField(max_length=20, null=True, blank=True)
    gst_reg_date = models.DateField(null=True, blank=True)
    gst_status = models.CharField(max_length=20, default="Active")
    email_id = models.EmailField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    msme_type = models.ForeignKey(
        CommonMaster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supplier_msme_profiles",
    )
    arn_no = models.CharField(max_length=100, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acc_year = models.CharField(max_length=20, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "supplier_profile"
        managed = False
        ordering = ["-id"]

    def __str__(self):
        return self.vendor_name


class SupplierContactPerson(UniqueIDMixin):
    supplier = models.ForeignKey(
        'SupplierProfile',
        on_delete=models.CASCADE,
        related_name='contact_persons'
    )

    person_name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile_no = models.CharField(max_length=15, null=True, blank=True)
    landline = models.CharField(max_length=20, null=True, blank=True)
    department = models.CharField(max_length=255, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, null=True, blank=True)

    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "supplier_contact_person"
        ordering = ["-id"]

    def __str__(self):
        return self.person_name


class SupplierStatutoryDetails(UniqueIDMixin):
    supplier = models.ForeignKey(
        'SupplierProfile',
        on_delete=models.CASCADE,
        related_name='statutory_details'
    )

    ecc_no = models.CharField(max_length=100, null=True, blank=True)
    commissionerate = models.CharField(max_length=255, null=True, blank=True)
    division = models.CharField(max_length=255, null=True, blank=True)
    range = models.CharField(max_length=255, null=True, blank=True)

    cst_no = models.CharField(max_length=100, null=True, blank=True)
    tin_no = models.CharField(max_length=100, null=True, blank=True)
    service_tax_no = models.CharField(max_length=100, null=True, blank=True)
    iec_code = models.CharField(max_length=100, null=True, blank=True)

    cin_no = models.CharField(max_length=100, null=True, blank=True)
    tan_no = models.CharField(max_length=100, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, null=True, blank=True)

    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "supplier_statutory_details"
        ordering = ["-id"]

    def __str__(self):
        return f"Statutory - {self.supplier.vendor_name}"


class SupplierAccountDetails(UniqueIDMixin):
    supplier = models.ForeignKey(
        'SupplierProfile',
        on_delete=models.CASCADE,
        related_name='account_details'
    )

    bank_name = models.CharField(max_length=255)
    account_no = models.CharField(max_length=50)
    account_holder_name = models.CharField(max_length=255)

    ifsc_code = models.CharField(max_length=20)
    contact_no = models.CharField(max_length=15, null=True, blank=True)

    bank_address = models.TextField(null=True, blank=True)
    swift_code = models.CharField(max_length=50, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, null=True, blank=True)

    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "supplier_account_details"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.bank_name} - {self.account_no}"

class SupplierBillingDetails(UniqueIDMixin):
    supplier = models.ForeignKey(
        'SupplierProfile',
        on_delete=models.CASCADE,
        related_name='billing_details'
    )

    name = models.CharField(max_length=255)
    address = models.TextField()

    # FK (master)
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True)

    # snapshot
    country_name = models.CharField(max_length=100, null=True, blank=True)
    state_name = models.CharField(max_length=100, null=True, blank=True)
    city_name = models.CharField(max_length=100, null=True, blank=True)

    contact_name = models.CharField(max_length=255, null=True, blank=True)
    contact_no = models.CharField(max_length=15, null=True, blank=True)

    gst_no = models.CharField(max_length=50, null=True, blank=True)
    gst_status = models.CharField(max_length=20, default="Active")

    ecc_no = models.CharField(max_length=50, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, null=True, blank=True)

    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "supplier_billing_details"
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        if self.country:
            self.country_name = self.country.name
        if self.state:
            self.state_name = self.state.name
        if self.city:
            self.city_name = self.city.name

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
class SupplierShippingDetails(UniqueIDMixin):
    supplier = models.ForeignKey(
        'SupplierProfile',
        on_delete=models.CASCADE,
        related_name='shipping_details'
    )

    name = models.CharField(max_length=255)
    address = models.TextField()

    # FK
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True)

    # snapshot
    country_name = models.CharField(max_length=100, null=True, blank=True)
    state_name = models.CharField(max_length=100, null=True, blank=True)
    city_name = models.CharField(max_length=100, null=True, blank=True)

    contact_name = models.CharField(max_length=255, null=True, blank=True)
    contact_no = models.CharField(max_length=15, null=True, blank=True)

    gst_no = models.CharField(max_length=50, null=True, blank=True)
    gst_status = models.CharField(max_length=20, default="Active")

    ecc_no = models.CharField(max_length=50, null=True, blank=True)

    # 🔥 important
    is_same_as_billing = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, null=True, blank=True)

    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "supplier_shipping_details"
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        if self.country:
            self.country_name = self.country.name
        if self.state:
            self.state_name = self.state.name
        if self.city:
            self.city_name = self.city.name

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
class SupplierDocuments(UniqueIDMixin):
    supplier = models.ForeignKey(
        'SupplierProfile',
        on_delete=models.CASCADE,
        related_name='documents'
    )

    document_type = models.CharField(max_length=100)

    file = models.FileField(upload_to='supplier_documents/')

    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    acc_year = models.CharField(max_length=20, null=True, blank=True)

    session_id = models.CharField(max_length=100, null=True, blank=True)
    sess_user_type = models.CharField(max_length=50, null=True, blank=True)
    sess_user_id = models.IntegerField(null=True, blank=True)
    sess_company_id = models.IntegerField(null=True, blank=True)
    sess_branch_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "supplier_documents"
        ordering = ["-id"]

    def __str__(self):
        return self.document_type
