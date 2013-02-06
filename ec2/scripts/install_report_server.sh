#!/bin/sh

# Assumes that "install_rpm_setup.sh" has already been run
source ./functions.sh

#
# Cloning git repo so the curl scripts under playpen are available for testing.
#
yum install -y git
cd ~
git clone https://github.com/splice/report_server.git

yum -y install report-server || {
    echo "yum install of report-server failed"
    exit 1;
}

chkconfig mongod on
service mongod start
chkconfig httpd on
service httpd on

echo "RPMs installed, waiting for mongo to initialize: `date`"
CMD="grep 'waiting for connections on port 27017' /var/log/mongodb/mongodb.log"
waitfor "${CMD}" "Waiting for mongodb to finish initialization" 10 30
echo "Completed check that mongo is available: `date`"

service httpd restart

