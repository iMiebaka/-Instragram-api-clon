# Generated by Django 3.1.3 on 2020-11-03 23:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uploads', '0013_auto_20201103_2307'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imagecomment',
            name='comment_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]