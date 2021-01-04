# Generated by Django 2.2 on 2020-10-07 11:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uploads', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewUploadMultiple',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=30, null=True)),
                ('created_on', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ImageGalery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_file', models.ImageField(upload_to='images/')),
                ('image_inst', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uploads.NewUploadMultiple')),
            ],
        ),
    ]
