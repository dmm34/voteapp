# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-10 01:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voteapp', '0012_menuitem'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MenuItem',
        ),
    ]
