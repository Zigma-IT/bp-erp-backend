import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr_master', '0005_levelmaster'),
    ]

    operations = [
        migrations.AddField(
            model_name='designationcreation',
            name='structure_type',
            field=models.CharField(
                choices=[('Grade Based', 'Grade Based'), ('Band Based', 'Band Based')],
                default='Grade Based',
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='designationcreation',
            name='grade_type',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='designationcreation',
            name='band',
            field=models.ForeignKey(
                blank=True,
                db_column='band_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='designations',
                to='hr_master.bandmaster',
            ),
        ),
        migrations.AddField(
            model_name='designationcreation',
            name='level',
            field=models.ForeignKey(
                blank=True,
                db_column='level_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='designations',
                to='hr_master.levelmaster',
            ),
        ),
    ]
