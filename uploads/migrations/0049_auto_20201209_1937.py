# Generated by Django 3.1.3 on 2020-12-09 19:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uploads', '0048_remove_newuploadmultiple_commentator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imagegalery',
            name='caption',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
