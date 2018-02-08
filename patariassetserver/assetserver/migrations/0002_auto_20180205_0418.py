# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-02-05 04:18
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('assetserver', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='derivativeimage',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='derivativeimage',
            name='identifier',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='masterimage',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='masterimage',
            name='external_identifier',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='masterimage',
            name='identifier',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
        ),
    ]
