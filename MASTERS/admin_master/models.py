from django.contrib.auth.hashers import make_password
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class UserType(models.Model):
    name = models.CharField(max_length=150, unique=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    under_users = models.CharField(max_length=150, null=True, blank=True)
    company_wise = models.BooleanField(default=False)
    project_wise = models.BooleanField(default=False)
    department_wise = models.BooleanField(default=False)
    user_wise = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TicketUserType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Staff(models.Model):
    name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class UserCreation(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)
    user_type = models.ForeignKey(UserType, on_delete=models.SET_NULL, null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    project = models.CharField(max_length=150, null=True, blank=True)
    under_users = models.CharField(max_length=150, null=True, blank=True)
    company = models.ForeignKey("common_master.Company", on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey("login_home.Department", on_delete=models.SET_NULL, null=True, blank=True)
    ticket_user_type = models.ForeignKey(TicketUserType, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_team_head = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    team_members = models.ManyToManyField("self", symmetrical=False, related_name="manages", blank=True)

    class Meta:
        db_table = "admin_master_usercreation"
        ordering = ["username"]

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)


class MainScreen(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=100, blank=True, null=True)
    status = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ScreenSection(models.Model):
    name = models.CharField(max_length=150)
    main_screen = models.ForeignKey(MainScreen, on_delete=models.CASCADE, related_name="sections")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserScreen(models.Model):
    main_screen = models.ForeignKey(MainScreen, on_delete=models.CASCADE)
    screen_section = models.ForeignKey(ScreenSection, on_delete=models.CASCADE)
    screen_name = models.CharField(max_length=150, db_index=True)
    folder_name = models.CharField(max_length=150, db_index=True)
    order_no = models.IntegerField(db_index=True)
    icon = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    can_add = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_list = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_view = models.BooleanField(default=False)
    can_print = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order_no"]

    def __str__(self):
        return self.screen_name


class UserTypePermission(models.Model):
    user_type = models.ForeignKey(UserType, on_delete=models.CASCADE)
    main_screen = models.ForeignKey(MainScreen, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=True)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user_type", "main_screen")
        ordering = ["user_type__name", "main_screen__name"]

    def __str__(self):
        return f"{self.user_type} - {self.main_screen}"
