#!/bin/sh

/sbin/restorecon -R /etc/httpd/conf.d/splice.conf
/sbin/restorecon -R /etc/splice
/sbin/restorecon -R /etc/pki/splice
/sbin/restorecon -R /etc/init.d/splice_all
/sbin/restorecon -R /etc/init.d/splice_celery
/sbin/restorecon -R /etc/init.d/splice_celerybeat
/sbin/restorecon -R /var/log/splice






