# Generated by Django 3.1.3 on 2020-12-25 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0034_auto_20201209_1945'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='sex',
            field=models.CharField(blank=True, choices=[('female', 'Female'), ('male', 'Male')], max_length=6, null=True),
        ),
    ]