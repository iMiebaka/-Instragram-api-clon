# Generated by Django 3.1.3 on 2020-11-09 12:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uploads', '0019_remove_newuploadmultiple_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='newuploadmultiple',
            name='commentator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='uploads.imagecomment'),
        ),
    ]
