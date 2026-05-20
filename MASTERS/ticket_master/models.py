import uuid
from django.db import models


class TaskCategory(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    department_unique_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    task_category_name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    description = models.TextField()

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    updated_user_id = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    updated = models.DateTimeField(
        auto_now=True
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
        db_table = "task_category"
        ordering = ['-id']

    def __str__(self):
        return self.task_category_name

class TaskSubCategory(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True
    )

    department_unique_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    task_category_name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    task_sub_category_name = models.TextField(
        null=True,
        blank=True
    )

    description = models.TextField()

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    updated_user_id = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    updated = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True
    )

    created_user_id = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    created = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    acc_year = models.CharField(max_length=50)

    session_id = models.CharField(max_length=50)

    sess_user_type = models.CharField(max_length=50)

    sess_user_id = models.CharField(max_length=50)

    sess_company_id = models.CharField(max_length=50)

    sess_branch_id = models.CharField(max_length=50)

    class Meta:
        db_table = "task_sub_category"

    def __str__(self):
        return str(self.task_sub_category_name)


class PriorityCreation(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=100,
        unique=True,
        editable=False
    )

    priority_name = models.CharField(
        max_length=100
    )

    priority_name_temp = models.CharField(
        max_length=100
    )

    priority_number = models.IntegerField()

    description = models.TextField()

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
        db_table = "priority_creation"

    def save(self, *args, **kwargs):

        if not self.unique_id:
            self.unique_id = str(uuid.uuid4())[:12]

        super().save(*args, **kwargs)

    def __str__(self):
        return self.priority_name


class ProblemType(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=100,
        unique=True,
        editable=False
    )

    category = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    sub_category = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    department = models.CharField(
        max_length=40,
        null=True,
        blank=True
    )

    problem_type = models.TextField(
        null=True,
        blank=True
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
        auto_now=True
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
        db_table = "problem_type"

    def save(self, *args, **kwargs):

        if not self.unique_id:
            self.unique_id = str(uuid.uuid4())[:12]

        super().save(*args, **kwargs)

    def __str__(self):
        return self.problem_type

class RemarkCreation(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False
    )

    remark_type = models.TextField(
        null=True,
        blank=True
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
        auto_now=True
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
        db_table = "remark_creation"

    def save(self, *args, **kwargs):

        if not self.unique_id:
            self.unique_id = str(uuid.uuid4())[:12]

        super().save(*args, **kwargs)

    def __str__(self):
        return self.remark_type