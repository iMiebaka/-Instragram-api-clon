# Generated by Django 3.1.3 on 2020-11-30 21:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0026_auto_20201130_2022'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='two_step_verification',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='sex',
            field=models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female')], max_length=6, null=True),
        ),
    ]