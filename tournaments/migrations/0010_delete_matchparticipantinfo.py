# Generated by Django 4.1.2 on 2024-10-26 10:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0009_rename_matchresult_matchstate_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MatchParticipantInfo',
        ),
    ]
