# Generated by Django 4.2 on 2023-05-13 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_alter_team_password_sent_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='seat',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='password_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]