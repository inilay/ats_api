# Generated by Django 4.1.2 on 2024-10-26 10:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0008_tournament_start_time'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='MatchResult',
            new_name='MatchState',
        ),
        migrations.RenameField(
            model_name='match',
            old_name='result',
            new_name='state',
        ),
    ]
