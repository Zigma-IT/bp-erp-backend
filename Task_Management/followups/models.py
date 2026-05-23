from django.db import models


class TaskFollowups(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(
        max_length=50,
        unique=True
    )

    task_no = models.CharField(max_length=50)

    status = models.CharField(max_length=50)

    tag_status = models.BooleanField(default=False)

    remarks_type = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    tagged_to = models.CharField(max_length=50)

    tagged_by = models.CharField(max_length=50)

    tag_remark = models.TextField(
        null=True,
        blank=True
    )

    tagged_datetime = models.DateTimeField()

    doc_type = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    uploads = models.TextField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    is_delete = models.BooleanField(default=False)

    updated_user_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    updated = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True
    )

    created_user_id = models.CharField(max_length=50)

    created = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
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
        db_table = 'task_followups'

    def __str__(self):
        return self.unique_id