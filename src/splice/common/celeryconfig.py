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
