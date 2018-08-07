# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.conf import settings
from django.db import models

MAX_LIST_SIZE = getattr(settings, 'LOGS_MAX_LIST_SIZE', 200)

if 'siteprefs' in settings.INSTALLED_APPS:
    # Respect those users who doesn't have siteprefs installed.
    from siteprefs.toolbox import patch_locals, register_prefs, pref

    patch_locals()  # That's bootstrap.

    register_prefs(
        pref(MAX_LIST_SIZE,
             verbose_name='Maximum number of logs shown to the user',
             static=False,
             field=models.IntegerField(blank=True)),
    )
