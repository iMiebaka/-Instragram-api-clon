# Generated by Django 3.1.3 on 2020-11-09 11:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploads', '0018_newuploadmultiple_comment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newuploadmultiple',
            name='comment',
        ),
    ]