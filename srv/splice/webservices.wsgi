import os
import sys
from splice import checkin_service

os.environ['DJANGO_SETTINGS_MODULE'] = 'checkin_service.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
