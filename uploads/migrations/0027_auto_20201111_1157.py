# Generated by Django 3.1.3 on 2020-11-11 11:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploads', '0026_alliancelist_created_on'),
    ]

    operations = [
        migrations.RenameField(
            model_name='alliancelist',
            old_name='followers',
            new_name='followering',
        ),
    ]
