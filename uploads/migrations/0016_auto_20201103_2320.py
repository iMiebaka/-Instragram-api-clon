# Generated by Django 3.1.3 on 2020-11-03 23:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uploads', '0015_auto_20201103_2315'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imagecomment',
            name='comment_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='commenter', to=settings.AUTH_USER_MODEL),
        ),
    ]
