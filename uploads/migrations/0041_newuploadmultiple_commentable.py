# Generated by Django 3.1.3 on 2020-12-02 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uploads', '0040_auto_20201202_1119'),
    ]

    operations = [
        migrations.AddField(
            model_name='newuploadmultiple',
            name='commentable',
            field=models.BooleanField(default=True),
        ),
    ]