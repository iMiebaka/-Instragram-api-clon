# Generated by Django 3.1.3 on 2020-12-09 19:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uploads', '0050_auto_20201209_1940'),
    ]

    operations = [
        migrations.AddField(
            model_name='newuploadmultiple',
            name='mini_caption',
            field=models.CharField(max_length=30, null=True),
        ),
    ]
