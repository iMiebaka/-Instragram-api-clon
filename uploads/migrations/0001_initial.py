# Generated by Django 2.2 on 2020-10-06 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NewUploads',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=30, null=True)),
                ('created_on', models.DateField(auto_now_add=True)),
                ('image_file', models.ImageField(upload_to='images/')),
            ],
        ),
    ]