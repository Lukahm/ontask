# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging.config
import sys

from .base import *  # NOQA

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATES[0]['OPTIONS'].update({'debug': True})

ALLOWED_HOSTS = ['*']

# Define STATIC_ROOT for the collectstatic command
STATIC_ROOT = join(BASE_DIR(), '..', 'site', 'static')

# Turn off debug while imported by Celery with a workaround
# See http://stackoverflow.com/a/4806384
if "celery" in sys.argv[0]:
    DEBUG = False

# Django Debug Toolbar
INSTALLED_APPS += (
    'debug_toolbar',)

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
if not TESTING:
    DEBUG_TOOLBAR_CONFIG = {
        # 'SHOW_TOOLBAR_CALLBACK': lambda r: True,  # enables it
        'SHOW_TOOLBAR_CALLBACK': lambda r: False,  # disables it
        # '...
    }

if DEBUG:
    print('BASE_DIR: ' + BASE_DIR())
    print('STATICFILES_DIRS: ' + ', '.join(STATICFILES_DIRS))
    print('MEDIA_ROOT: ' + MEDIA_ROOT)
    print('MEDIA_URL: ' + MEDIA_URL)
    print('ONTASK_HELP_URL: ' + ONTASK_HELP_URL)

# Additional middleware introduced by debug toolbar
MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',)

# Show emails to console in DEBUG mode
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Show thumbnail generation errors
THUMBNAIL_DEBUG = True

# Allow internal IPs for debugging
INTERNAL_IPS = [
    '127.0.0.1',
    '0.0.0.1',
    'localhost',
]

# Log everything to the logs directory at the top
LOGFILE_ROOT = join(BASE_DIR(), '..', 'logs')

# Reset logging
# (see http://www.caktusgroup.com/blog/2015/01/27/Django-Logging-Configuration-logging_config-default-settings-logger/)

LOGGING_CONFIG = None
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(pathname)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'django_log_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': join(LOGFILE_ROOT, 'django.log'),
            'formatter': 'verbose'
        },
        'proj_log_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': join(LOGFILE_ROOT, 'project.log'),
            'formatter': 'verbose'
        },
        'script_log_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': join(LOGFILE_ROOT, 'script.log'),
            'formatter': 'verbose'
        },
        'scheduler_log_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': join(LOGFILE_ROOT, 'scheduler.log'),
            'formatter': 'verbose'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['django_log_file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'project': {
            'handlers': ['proj_log_file'],
            'level': 'DEBUG',
        },
        'scripts': {
            'handlers': ['script_log_file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'scripts.scheduler': {
            'handlers': ['scheduler_log_file'],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}

logging.config.dictConfig(LOGGING)
