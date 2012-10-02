# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


# Django settings for checkin_service project.
import os
import pwd


from logging import getLogger
_LOG = getLogger(__name__)

# Initialize Splice Config
from splice.common import config
config.init()


def get_username():
    return pwd.getpwuid( os.getuid() )[ 0 ]
# Set DEPLOYED to True if this is running under apache with mod_wsgi
# We will attempt to detect this automatically and change

DEPLOYED=True # Setting to True so when celeryd runs and loads this it will use same settings as apache
if get_username().lower() == "apache":
    DEPLOYED=True


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': "",                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'g6oax61oxoljlw6koj4-d^%n0i_0-8n^inbi0kbhb2!58%pe*v'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
     'splice.common.middleware.ProfileMiddleware',
)

ROOT_URLCONF = 'splice.checkin_service.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'splice.checkin_service.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    # commented out 'django.contrib.auth' to 'django.contrib.staticfiles' to fix below when running tests.
    #    settings.DATABASES is improperly configured. Please supply the ENGINE value
    #'django.contrib.auth',
    #'django.contrib.contenttypes',
    #'django.contrib.sessions',
    #'django.contrib.sites',
    #'django.contrib.messages',
    #'django.contrib.staticfiles',

    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'tastypie',
    'splice.entitlement',
    'djcelery',
    'rhic_serve.rhic_rcs',
)

LOG_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "debug_logs")
if DEPLOYED:
    LOG_DIR = "/var/log/splice"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'log_file':{
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'django.log'),
            'maxBytes': '16777216',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'splice': {
            'handlers': ['log_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'root': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO'
        },
    }
}

##
## Adding mongoengine specifics ##
##
MONGO_DATABASE_NAME = 'checkin_service'
import mongoengine
mongoengine.connect(MONGO_DATABASE_NAME)
mongoengine.register_connection("rhic_serve", MONGO_DATABASE_NAME)

AUTHENTICATION_BACKENDS = (
    'mongoengine.django.auth.MongoEngineBackend',
)
SESSION_ENGINE = 'mongoengine.django.sessions'
##
## End mongoengine specifics
##

#############################
# Celery Configuration
#
import djcelery
djcelery.setup_loader()

from splice.common.constants import SPLICE_ENTITLEMENT_BASE_TASK_NAME
## Broker settings.
BROKER_URL = "amqp://guest:guest@localhost:5672//"
# List of modules to import when celery starts.
CELERY_IMPORTS = ("splice.entitlement.tasks", )
## Using the database to store task state and results.
CELERY_RESULT_BACKEND = "mongodb"
CELERY_MONGODB_BACKEND_SETTINGS = {
    "host": "localhost"
}
CELERY_ANNOTATIONS = {"%s.add" % (SPLICE_ENTITLEMENT_BASE_TASK_NAME): {"rate_limit": "10/s"}}


rhic_serve_cfg = config.get_rhic_serve_config_info()

single_rhic_retry_lookup_tasks_in_minutes = 15
if rhic_serve_cfg.has_key("single_rhic_retry_lookup_tasks_in_minutes"):
    single_rhic_retry_lookup_tasks_in_minutes = int(rhic_serve_cfg["single_rhic_retry_lookup_tasks_in_minutes"])

from datetime import timedelta
CELERYBEAT_SCHEDULE = {
    # Executes every 30 seconds
    #'dummy_task_executes_every_hour': {
    #    'task': '%s.log_time' % (SPLICE_ENTITLEMENT_BASE_TASK_NAME),
    #    'schedule': timedelta(seconds=5),
    #    'args': None,
    #},
    'process_running_rhic_lookup_tasks': {
        'task': '%s.process_running_rhic_lookup_tasks' % (SPLICE_ENTITLEMENT_BASE_TASK_NAME),
        'schedule': timedelta(minutes=single_rhic_retry_lookup_tasks_in_minutes),
       'args': None,
    }
}
CELERY_TIMEZONE = 'UTC'

# Controls 'if' we will sync all rhics
sync_all_rhics_bool = True
if rhic_serve_cfg.has_key("sync_all_rhics_bool"):
    sync_all_rhics_bool = rhic_serve_cfg["sync_all_rhics_bool"]
if sync_all_rhics_bool:
    # Controls 'when' we will run a full sync of rhics
    sync_all_rhics_in_minutes = 60
    if rhic_serve_cfg.has_key("sync_all_rhics_in_minutes"):
        sync_all_rhics_in_minutes = int(rhic_serve_cfg["sync_all_rhics_in_minutes"])
    CELERYBEAT_SCHEDULE['sync_all_rhics'] = {
        'task': '%s.sync_all_rhics' % (SPLICE_ENTITLEMENT_BASE_TASK_NAME),
        'schedule': timedelta(minutes=sync_all_rhics_in_minutes),
        'args': None,
    }
#
# End of Celery Configuration
#############################
