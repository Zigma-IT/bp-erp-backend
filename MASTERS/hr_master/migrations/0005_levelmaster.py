from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr_master', '0004_bandmaster'),
    ]

    operations = [
        migrations.CreateModel(
            name='LevelMaster',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('band', models.ForeignKey(
                    db_column='band_id',
                    on_delete=django.db.models.deletion.PROTECT,
                    to='hr_master.bandmaster',
                )),
                ('level_name', models.CharField(max_length=100)),
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
                'db_table': 'level_master',
            },
        ),
    ]
