python /git/splice-server/src/splice/manage.py celerybeat --schedule=/var/run/splice/celerybeat_schedule -l debug -f /var/log/splice/celery/celerybeat.log --uid splice --gid splice --workdir /git/splice-server/src/splice --detach --pidfile=/var/run/splice/celerybeat.pid

#
# Attempt with --detach removed
#
#python /git/splice-server/src/splice/manage.py celerybeat --schedule=/var/run/splice/celerybeat_schedule -l debug -f /var/log/splice/celery/celerybeat.log --uid splice --gid splice --workdir /git/splice-server/src/splice --pidfile=/var/run/splice/celerybeat.pid


