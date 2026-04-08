from django.db import models


class Continent(models.Model):
    name = models.CharField(max_length=100, unique=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Country(models.Model):
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

    class Meta:
        unique_together = ("name", "code")
        ordering = ["name"]

    def __str__(self):
        return self.name


class State(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="states",
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("country", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


class CommonMaster(models.Model):
    type = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "common_master"
        ordering = ["type", "name"]

    def __str__(self):
        return self.name

#City
class City(models.Model):
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

    class Meta:
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
class Tax(models.Model):
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

    class Meta:
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
class Company(models.Model):
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

    class Meta:
        db_table = "common_master_CompanyCreation"
        ordering = ["-id"]

    def __str__(self):
        return self.name
    

# Project Creation
class Project(models.Model):
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

    class Meta:
        db_table = "common_master_ProjectCreation"
        ordering = ["-id"]

    def __str__(self):
        return self.name