# models.py

import uuid
from django.contrib.auth.hashers import make_password
from django.db import models


# =========================================================
# COMMON MIXIN
# =========================================================

class UniqueIDMixin(models.Model):

    unique_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    class Meta:
        abstract = True


# =========================================================
# ROLE
# =========================================================

class Role(UniqueIDMixin):

    name = models.CharField(max_length=100)

    class Meta:
        db_table = "admin_master_role"

    def __str__(self):
        return self.name


# =========================================================
# USER TYPE
# =========================================================

class UserType(UniqueIDMixin):

    name = models.CharField(
        max_length=150,
        unique=True,
        db_index=True
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True
    )

    under_users = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )

    company_wise = models.BooleanField(default=False)
    project_wise = models.BooleanField(default=False)
    department_wise = models.BooleanField(default=False)
    user_wise = models.BooleanField(default=False)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "admin_master_usertype"
        ordering = ["name"]

    def __str__(self):
        return self.name


# =========================================================
# TICKET USER TYPE
# =========================================================

class TicketUserType(UniqueIDMixin):

    name = models.CharField(max_length=100)

    class Meta:
        db_table = "admin_master_ticketusertype"

    def __str__(self):
        return self.name


# =========================================================
# STAFF
# =========================================================

class Staff(UniqueIDMixin):

    name = models.CharField(max_length=150)

    mobile = models.CharField(max_length=15)

    class Meta:
        db_table = "admin_master_staff"

    def __str__(self):
        return self.name


# =========================================================
# USER CREATION
# =========================================================

class UserCreation(UniqueIDMixin):

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE
    )

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE
    )

    username = models.CharField(
        max_length=150,
        unique=True
    )

    password = models.CharField(
        max_length=255
    )

    user_type = models.ForeignKey(
        UserType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    mobile = models.CharField(
        max_length=15,
        null=True,
        blank=True
    )

    project = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )

    under_users = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )

    company = models.ForeignKey(
        "common_master.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    department = models.ForeignKey(
        "login_home.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    ticket_user_type = models.ForeignKey(
        TicketUserType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    is_team_head = models.BooleanField(default=False)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    team_members = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="manages",
        blank=True
    )

    class Meta:
        db_table = "admin_master_usercreation"
        ordering = ["username"]

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):

        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)

        super().save(*args, **kwargs)


# =========================================================
# MAIN SCREEN
# =========================================================

class MainScreen(UniqueIDMixin):

    name = models.CharField(
        max_length=150,
        unique=True
    )

    code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    folder_key = models.SlugField(
        max_length=150,
        unique=True,
        db_index=True,
        blank=True,
        null=True
    )

    screen_type = models.CharField(
        max_length=20,
        default="Mega Menu"
    )

    order_no = models.IntegerField(
        default=0,
        db_index=True
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    status = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        null=True
    )

    class Meta:
        db_table = "admin_master_mainscreen"
        ordering = ["order_no", "name"]

    def __str__(self):
        return self.name


# =========================================================
# SCREEN SECTION
# =========================================================

class ScreenSection(UniqueIDMixin):

    name = models.CharField(
        max_length=150
    )

    main_screen = models.ForeignKey(
        'MainScreen',
        on_delete=models.CASCADE,
        related_name="screen_sections"
    )

    order_no = models.IntegerField(
        default=0,
        db_index=True
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        null=True
    )

    class Meta:
        db_table = "admin_master_screensection"
        ordering = ["order_no", "id"]
       
    def __str__(self):
        return self.name


# =========================================================
# USER SCREEN
# =========================================================

class UserScreen(UniqueIDMixin):

    main_screen = models.ForeignKey(
        'MainScreen',
        on_delete=models.CASCADE
    )

    screen_section = models.ForeignKey(
        'ScreenSection',
        on_delete=models.CASCADE
    )

    screen_name = models.CharField(
        max_length=150,
        db_index=True
    )

    folder_name = models.CharField(
        max_length=150,
        db_index=True
    )

    order_no = models.IntegerField(
        db_index=True
    )

    icon = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True
    )

    can_add = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_list = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_view = models.BooleanField(default=False)
    can_print = models.BooleanField(default=False)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "admin_master_userscreen"
        ordering = ["order_no"]
       
    def __str__(self):
        return self.screen_name


# =========================================================
# USER TYPE PERMISSION
# =========================================================

class UserTypePermission(UniqueIDMixin):

    user_type = models.ForeignKey(
        UserType,
        on_delete=models.CASCADE
    )

    main_screen = models.ForeignKey(
        'MainScreen',
        on_delete=models.CASCADE
    )

    user_screen = models.ForeignKey(
        'UserScreen',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    can_view = models.BooleanField(default=True)
    can_add = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_list = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_print = models.BooleanField(default=False)

    status = models.BooleanField(default=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "admin_master_usertypepermission"

        unique_together = (
            "user_type",
            "user_screen"
        )

        ordering = [
            "user_type__name",
            "main_screen__name",
            "user_screen__order_no"
        ]

    def __str__(self):
        return f"{self.user_type} - {self.user_screen or self.main_screen}"
