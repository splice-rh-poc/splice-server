#!/bin/sh

# Assumes that "install_rpm_setup.sh" has already been run
source ./functions.sh

#
# Cloning git repo so the curl scripts under playpen are available for testing.
#
yum install -y git
cd ~
git clone https://github.com/splice/splice-server.git

yum -y install splice || {
    echo "yum install of splice failed"
    exit 1;
}

yum -y install splice-certmaker || {
    echo "yum install of splice-certmaker failed"
    exit 1;
}

chkconfig rabbitmq-server on
service rabbitmq-server start
chkconfig mongod on
service mongod start
chkconfig splice-certmaker on
service splice-certmaker restart

echo "RPMs installed, waiting for mongo & splice-certmaker to initialize: `date`"
CMD="grep 'waiting for connections on port 27017' /var/log/mongodb/mongodb.log"
waitfor "${CMD}" "Waiting for mongodb to finish initialization" 10 30
echo "Completed check that mongo is available: `date`"

# Ensure splice-certmaker is up 
CMD="grep 'org.candlepin.splice.Main - server started!' /var/log/splice/splice-certmaker.log"
waitfor "${CMD}" "Waiting for splice-certmaker to come up" 8 15
echo "Completed check that splice-certmaker is up: `date`"

service splice_all stop
service splice_all start



