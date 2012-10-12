#!/bin/sh

NAME="splice-server"
SELINUX_VARIANTS="targeted"
if [ $# -lt 1 ]; then
    INSTALL_DIR=/usr/share
else
    INSTALL_DIR=$1
fi


if /usr/sbin/selinuxenabled ; then
    for selinuxvariant in ${SELINUX_VARIANTS}
    do
        /usr/sbin/semanage -i - << _EOF
            module -a ${INSTALL_DIR}/selinux/${selinuxvariant}/${NAME}.pp
            boolean -m --on httpd_can_network_connect
_EOF
done
fi
