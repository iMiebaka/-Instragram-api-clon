# Generated by Django 3.1.3 on 2020-12-09 16:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uploads', '0046_likecomment'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagecomment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='uploads.imagecomment'),
        ),
    ]
