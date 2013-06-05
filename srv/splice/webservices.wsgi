import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'splice.checkin_service.settings'

#import djcelery
#djcelery.setup_loader()

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
