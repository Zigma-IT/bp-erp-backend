from django.db import models


class TaskCreation(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True
    )

    task_code = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    company_id = models.CharField(max_length=50)

    project_id = models.CharField(max_length=50)

    department_id = models.CharField(max_length=50)

    task_category_id = models.CharField(max_length=50)

    task_sub_category_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    problem_type = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    impact_type = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    target_date = models.DateField(
        null=True,
        blank=True
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    acc_year = models.CharField(max_length=50)

    session_id = models.CharField(max_length=50)

    sess_user_type = models.CharField(max_length=50)

    sess_user_id = models.CharField(max_length=50)

    sess_company_id = models.CharField(max_length=50)

    sess_branch_id = models.CharField(max_length=50)

    status = models.CharField(
        max_length=50,
        default='Open'
    )

    priority = models.CharField(
        max_length=50,
        default='Normal'
    )

    is_internal_task = models.BooleanField(
        default=False
    )

    assigned_to = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    created_date = models.DateTimeField(
        auto_now_add=True
    )

    created_user_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    updated_date = models.DateTimeField(
        auto_now=True
    )

    updated_user_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    is_delete = models.BooleanField(
        default=False
    )

    class Meta:

        db_table = 'task_creation'

        ordering = ['-id']

    def __str__(self):

        return self.unique_id


class SelfTask(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(max_length=50, unique=True)

    task_code = models.CharField(
        max_length=130,
        null=True,
        blank=True
    )

    company_id = models.CharField(max_length=50)

    project_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    priority = models.CharField(
        max_length=20,
        default='Medium'
    )

    target_date = models.DateField(
        null=True,
        blank=True
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=10,
        default='0'
    )

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    created_date = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    created_user_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    updated_date = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True
    )

    updated_user_id = models.CharField(
        max_length=50,
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
        db_table = 'self_task'

    def __str__(self):
        return self.unique_id