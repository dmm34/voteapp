# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-08 22:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voteapp', '0006_auto_20170308_1522'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ballot',
            name='ballot_instruction',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='ballot',
            name='ballot_short_desc',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
