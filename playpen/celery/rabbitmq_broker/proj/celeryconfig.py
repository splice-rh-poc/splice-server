## Broker settings.
BROKER_URL = "amqp://guest:guest@localhost:5672//"

# List of modules to import when celery starts.
CELERY_IMPORTS = ("tasks", )

## Using the database to store task state and results.
CELERY_RESULT_BACKEND = "mongodb"
CELERY_MONGODB_BACKEND_SETTINGS = {
    "host": "localhost"
}

CELERY_ANNOTATIONS = {"tasks.add": {"rate_limit": "10/s"}}
