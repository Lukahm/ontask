# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-30 03:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataops', '0020_auto_20180530_1314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sqlconnection',
            name='db_password',
            field=models.BooleanField(default=False, verbose_name='Requires password?'),
        ),
    ]
