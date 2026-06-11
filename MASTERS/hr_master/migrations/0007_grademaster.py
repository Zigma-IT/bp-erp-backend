from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr_master', '0006_designationcreation_structure_band_level'),
    ]

    operations = [
        migrations.CreateModel(
            name='GradeMaster',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('grade_name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('is_delete', models.BooleanField(default=False)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('acc_year', models.CharField(max_length=50)),
                ('session_id', models.CharField(max_length=50)),
                ('sess_user_type', models.CharField(max_length=50)),
                ('sess_user_id', models.CharField(max_length=50)),
                ('sess_company_id', models.CharField(max_length=50)),
                ('sess_branch_id', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'grade_master',
            },
        ),
    ]
