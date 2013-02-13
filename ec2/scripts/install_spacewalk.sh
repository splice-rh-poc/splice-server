#!/bin/sh
source ./functions.sh

export ANSWER_FILE="/tmp/spacewalk.answers"

# Set hostname of instance to EC2 public hostname
HOSTNAME=`curl -s http://169.254.169.254/latest/meta-data/public-hostname`
hostname ${HOSTNAME}
sed -i "s/^HOSTNAME.*/HOSTNAME=${HOSTNAME}/" /etc/sysconfig/network

# Install Spacewalk
rpm -q spacewalk-repo &> /dev/null
if [ $? -eq 1 ]; then
    rpm -Uvh http://yum.spacewalkproject.org/1.8/RHEL/6/x86_64/spacewalk-repo-1.8-4.el6.noarch.rpm || {
        echo "Unable to install Spacewalk RPM"
        exit 1;
    }
fi

# Install EPEL
rpm -q epel-release &> /dev/null
if [ $? -eq 1 ]; then
    rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm || {
        echo "Unable to install EPEL"
        exit 1;
    }
fi


if [ ! -f /etc/yum/repos.d/jpackage-generic.repo ]; then
    cat > /etc/yum.repos.d/jpackage-generic.repo << EOF
[jpackage-generic]
name=JPackage generic
#baseurl=http://mirrors.dotsrc.org/pub/jpackage/5.0/generic/free/
mirrorlist=http://www.jpackage.org/mirrorlist.php?dist=generic&type=free&release=5.0
enabled=1
gpgcheck=1
gpgkey=http://www.jpackage.org/jpackage.asc
EOF
fi

yum install -y spacewalk-setup-embedded-postgresql
yum install -y spacewalk-postgresql

spacewalk-setup --disconnected --answer-file="${ANSWER_FILE}"

