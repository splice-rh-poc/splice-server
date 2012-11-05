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


"""
Django settings for checkin_service project.
"""

from datetime import timedelta
import os
import pwd

from splice.common.settings import *

def get_username():
    return pwd.getpwuid( os.getuid() )[ 0 ]
# Set DEPLOYED to True if this is running under apache with mod_wsgi
# We will attempt to detect this automatically and change

DEPLOYED=True # Setting to True so when celeryd runs and loads this it will use same settings as apache
if get_username().lower() == "apache":
    DEPLOYED=True

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'g6oax61oxoljlw6koj4-d^%n0i_0-8n^inbi0kbhb2!58%pe*v'

ROOT_URLCONF = 'splice.checkin_service.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'splice.checkin_service.wsgi.application'

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
import mongoengine
MONGO_DATABASE_NAME = config.CONFIG.get('server', 'db_name')
MONGO_DATABASE_HOST = config.CONFIG.get('server', 'db_host')
mongoengine.connect(MONGO_DATABASE_NAME, host=MONGO_DATABASE_HOST)
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

CELERY_TIMEZONE = 'UTC'

CELERYBEAT_SCHEDULE = {}

def set_celerybeat_schedule():
    global CELERYBEAT_SCHEDULE
    CELERYBEAT_SCHEDULE = {}

    rhic_serve_cfg = config.get_rhic_serve_config_info()

    single_rhic_retry_lookup_tasks_in_minutes = 15
    if rhic_serve_cfg.has_key("single_rhic_retry_lookup_tasks_in_minutes"):
        single_rhic_retry_lookup_tasks_in_minutes = rhic_serve_cfg["single_rhic_retry_lookup_tasks_in_minutes"]

    CELERYBEAT_SCHEDULE = {
        # Executes every 30 seconds
        'process_running_rhic_lookup_tasks': {
            'task': '%s.process_running_rhic_lookup_tasks' % (SPLICE_ENTITLEMENT_BASE_TASK_NAME),
            'schedule': timedelta(minutes=single_rhic_retry_lookup_tasks_in_minutes),
           'args': None,
        }
    }

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
    else:
        LOG.warning("Skipped configuring a periodic task to upload Product Usage since no servers were configured.")

    LOG.debug("CeleryBeat configuration: %s" % (CELERYBEAT_SCHEDULE))

set_celerybeat_schedule()

#
# End of Celery Configuration
#############################
