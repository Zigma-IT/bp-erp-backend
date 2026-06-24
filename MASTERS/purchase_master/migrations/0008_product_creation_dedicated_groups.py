"""
Replace the shared ProductGroup/ProductSubGroup FK columns on ProductCreation
with brand-new, completely isolated tables (product_creation_group and
product_creation_subgroup) that have zero connection to any master table.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchase_master', '0007_alter_itemmaster_options_and_more'),
    ]

    operations = [
        # 1. Create dedicated ProductCreationGroup table
        migrations.CreateModel(
            name='ProductCreationGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'product_creation_group',
                'ordering': ['name'],
            },
        ),

        # 2. Create dedicated ProductCreationSubGroup table
        migrations.CreateModel(
            name='ProductCreationSubGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sub_groups',
                    to='purchase_master.productcreationgroup',
                )),
            ],
            options={
                'db_table': 'product_creation_subgroup',
                'ordering': ['name'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='productcreationsubgroup',
            unique_together={('group', 'name')},
        ),

        # 3. Add new isolated FK columns to ProductCreation
        migrations.AddField(
            model_name='productcreation',
            name='product_group',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='products',
                to='purchase_master.productcreationgroup',
            ),
        ),
        migrations.AddField(
            model_name='productcreation',
            name='product_sub_group',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='products',
                to='purchase_master.productcreationsubgroup',
            ),
        ),

        # 4. Remove old FK columns that pointed to the shared ProductGroup/ProductSubGroup tables
        migrations.RemoveField(
            model_name='productcreation',
            name='group',
        ),
        migrations.RemoveField(
            model_name='productcreation',
            name='sub_group',
        ),
    ]
