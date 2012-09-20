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


from splice.checkin_service import settings
#Inheriting configuration from 'settings.py'

## Broker settings.
BROKER_URL = settings.BROKER_URL

# List of modules to import when celery starts.
CELERY_IMPORTS = settings.CELERY_IMPORTS

## Using the database to store task state and results.
CELERY_RESULT_BACKEND = settings.CELERY_RESULT_BACKEND
CELERY_MONGODB_BACKEND_SETTINGS = settings.CELERY_MONGODB_BACKEND_SETTINGS

CELERY_ANNOTATIONS = settings.CELERY_ANNOTATIONS
