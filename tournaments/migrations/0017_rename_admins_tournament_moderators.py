# Generated by Django 4.1.2 on 2025-02-07 16:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0016_tournament_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tournament',
            old_name='admins',
            new_name='moderators',
        ),
    ]
