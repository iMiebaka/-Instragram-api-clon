# Generated by Django 3.1.3 on 2020-11-13 17:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uploads', '0032_savedmedia_created_on'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaggedUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('added_media', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='taggable_media', to='uploads.newuploadmultiple')),
                ('users_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_tbt', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
