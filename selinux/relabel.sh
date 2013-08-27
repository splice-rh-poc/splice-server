#!/bin/sh

/sbin/restorecon -R /srv/splice
/sbin/restorecon -R /etc/httpd/conf.d/splice.conf
/sbin/restorecon -R /etc/splice
/sbin/restorecon -R /etc/pki/splice
/sbin/restorecon -R /etc/init.d/splice_all
/sbin/restorecon -R /var/log/splice






