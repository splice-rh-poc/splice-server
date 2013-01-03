SERVER_ADDR=ec2-23-22-86-129.compute-1.amazonaws.com
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
# HACK until we fix perms of log files to share with splice-certmaker
CERTMAKER_LOG="/var/log/splice/splice-certmaker.log"
touch ${CERTMAKER_LOG}
chown splice:apache ${CERTMAKER_LOG}
chmod ug+rwX ${CERTMAKER_LOG}
# End of Hack
chkconfig splice-certmaker on
service splice-certmaker restart

echo "RPMs installed, waiting for mongo & splice-certmaker to initialize: `date`"
# Ensure mongodb is up (sometimes it takes 30 seconds to finish it's first run)
OVER=0
TESTS=0
MAX_TESTS=10
while [ $OVER != 1 ] && [ $TESTS -lt $MAX_TESTS ]; do
    OUTPUT=`grep 'waiting for connections on port 27017' /var/log/mongodb/mongodb.log`
    RET_CODE=$?
    if [ RET_CODE == 0 ]; then
        OVER=1
    else
        # I like bc but 'echo $(( TESTS+=1 ))' should work, too. Or expr.
        TESTS=$(echo $TESTS+1 | bc)
        echo "Waiting for mongodb to finish initialization"
        sleep 30
    fi
done
if [ $TESTS = $MAX_TESTS ]; then
    echo "Mongo has not come up after 5 minutes.  Unexpected error"
    exit 1
fi
echo "Completed check that mongo is available: `date`"

# Ensure splice-certmaker is up 
OVER=0
TESTS=0
MAX_TESTS=12
while [ $OVER != 1 ] && [ $TESTS -lt $MAX_TESTS ]; do
    OUTPUT=`grep 'org.candlepin.splice.Main - server started!' /var/log/splice/splice-certmaker.log`
    RET_CODE=$?
    if [ RET_CODE == 0 ]; then
        OVER=1
    else
        # I like bc but 'echo $(( TESTS+=1 ))' should work, too. Or expr.
        TESTS=$(echo $TESTS+1 | bc)
        echo "Waiting for splice-certmaker to come up"
        sleep 5
    fi
done
if [ $TESTS = $MAX_TESTS ]; then
    echo "splice-certmaker has not come up after 60 seconds.  Unexpected error"
    exit 1
fi
echo "Completed check that splice-certmaker is up: `date`"

service splice_all stop
service splice_all start



