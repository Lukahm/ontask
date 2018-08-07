# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-29 22:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataops', '0011_auto_20180526_1430'),
    ]

    operations = [
        migrations.CreateModel(
            name='SQLConnection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=2048, unique=True, verbose_name='Connection name')),
                ('description_text', models.CharField(blank=True, default='', max_length=2048, verbose_name='Connection description')),
                ('conn_type', models.CharField(help_text='Postgresql, Mysql, etc.', max_length=2048, verbose_name='Connection type')),
                ('db_user', models.CharField(blank=True, default='', max_length=2048, verbose_name='User name')),
                ('db_password', models.CharField(blank=True, default='', max_length=65536, verbose_name='Password')),
                ('db_host', models.CharField(blank=True, default='', max_length=2048, verbose_name='Host')),
                ('ncols', models.IntegerField(blank=True, null=True, verbose_name='Port')),
                ('db_name', models.CharField(default='', max_length=2048)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
    ]
