# Generated by Django 3.1.3 on 2020-11-23 18:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_auto_20201115_1630'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='sex',
            field=models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female')], max_length=6, null=True),
        ),
    ]
