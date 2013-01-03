#!/bin/sh
# Hostname for instance serving splice RPMs
SERVER_ADDR=ec2-23-22-86-129.compute-1.amazonaws.com

function waitfor() {
    if [ "$#" -ne 4 ]; then
        echo "Incorrect usage of waitfor() function, only $# arguments passed when 4 were expected"
        echo "Usage: retry CMD WAITING_MESSAGE NUM_ITERATIONS SLEEP_SECONDS_EACH_ITERATION"
        exit 1
    fi
    CMD=$1
    WAITING_MSG=$2
    MAX_TESTS=$3
    SLEEP_SECS=$4
    
    TESTS=0
    OVER=0
    while [ $OVER != 1 ] && [ $TESTS -lt $MAX_TESTS ]; do
        eval ${CMD} > /dev/null
        if [ $? -eq 0 ]; then
            OVER=1
        else
            TESTS=$(echo $TESTS+1 | bc)
            echo $WAITING_MSG will wait for ${SLEEP_SECS} seconds this is attempt ${TESTS}/${MAX_TESTS} at `date`
            sleep $SLEEP_SECS
        fi
    done
    if [ $TESTS = $MAX_TESTS ]; then
        echo ""
        echo "**ERROR**:"
        echo "Command:  ${CMD}"
        echo "Unsuccessful after ${MAX_TESTS} iterations with a sleep of ${SLEEP_SECS} seconds in between"
        exit 1
    fi
}

# Install EPEL
rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm || {
    echo "Unable to install EPEL"
    exit 1;
}
# Install Splice RPMs
wget http://${SERVER_ADDR}/pub/splice_el6_x86_64.repo -O /etc/yum.repos.d/splice_el6_x86_64.repo || {
    echo "Unable to download the yum repo configuration for splice: splice.repo"
    exit 1;
}

# Set hostname of instance to EC2 public hostname
HOSTNAME=`curl -s http://169.254.169.254/latest/meta-data/public-hostname`
hostname ${HOSTNAME}
sed -i "s/^HOSTNAME.*/HOSTNAME=${HOSTNAME}/" /etc/sysconfig/network

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



