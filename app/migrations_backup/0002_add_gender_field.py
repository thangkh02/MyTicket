# Generated by Django 5.1.7 on 2025-04-08 02:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='gender',
            field=models.CharField(blank=True, choices=[('M', 'Nam'), ('F', 'Nữ')], max_length=1, null=True, verbose_name='Giới tính'),
        ),
    ]
