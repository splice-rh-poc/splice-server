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
import logging
import logging.config
import os
import pwd


# Initialize Splice Config & Logging
SPLICE_CONFIG_FILE = '/etc/splice/server.conf'
from splice.common import config
config.init()
splice_log_cfg = config.get_logging_config_file()
if splice_log_cfg:
    if not os.path.exists(splice_log_cfg):
        print "Unable to read '%s' for logging configuration" % (splice_log_cfg)
    else:
        logging.config.fileConfig(splice_log_cfg)
from logging import getLogger
_LOG = getLogger(__name__)


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
    # 'splice.common.middleware.WsgiLogErrors',
    'splice.common.middleware.StandardExceptionMiddleware',
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
    'report_server.report_import',
)


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

report_info = config.get_reporting_config_info()
if report_info["servers"]:
    CELERYBEAT_SCHEDULE['upload_product_usage'] = {
        'task': '%s.upload_product_usage' % (SPLICE_ENTITLEMENT_BASE_TASK_NAME),
        'schedule': timedelta(minutes=report_info["upload_interval_minutes"]),
        'args': None,
    }
_LOG.debug("CeleryBeat configuration: %s" % (CELERYBEAT_SCHEDULE))
#
# End of Celery Configuration
#############################

#
# TODO: See if we can work out a better solution and not need to set
#       real values to the below cert settings for 'rhic-serve'
#       RCS is not specifically using the functionality requiring these settings, yet if they are
#       not defined, and not pointing to a real file to read then an exception is thrown immediately and
#       requests will not be processed
#
CA_CERT_PATH="/etc/pki/splice/Splice_testing_root_CA.crt"
CA_KEY_PATH="/etc/pki/splice/Splice_testing_root_CA.key"
CERT_DAYS="1"
