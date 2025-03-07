# Generated by Django 4.1.2 on 2024-11-24 11:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tournaments', '0012_participantresult'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchparticipantinfo',
            name='participant_result',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='tournaments.participantresult'),
            preserve_default=False,
        ),
    ]
