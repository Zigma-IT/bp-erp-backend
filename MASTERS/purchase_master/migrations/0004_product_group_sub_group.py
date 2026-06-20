import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("purchase_master", "0003_standardbom_semi_finished_nullable_product"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("unique_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("group_name", models.CharField(max_length=100, unique=True)),
                ("code", models.CharField(max_length=20, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["group_name"],
            },
        ),
        migrations.CreateModel(
            name="ProductSubGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("unique_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("sub_group_name", models.CharField(max_length=100)),
                ("sub_group_code", models.CharField(max_length=20)),
                ("description", models.TextField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sub_groups",
                        to="purchase_master.productgroup",
                    ),
                ),
            ],
            options={
                "ordering": ["sub_group_name"],
                "abstract": False,
                "unique_together": {("group", "sub_group_name")},
            },
        ),
        migrations.AlterField(
            model_name="productcreation",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="purchase_master.productgroup",
            ),
        ),
        migrations.AlterField(
            model_name="productcreation",
            name="sub_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="purchase_master.productsubgroup",
            ),
        ),
    ]
