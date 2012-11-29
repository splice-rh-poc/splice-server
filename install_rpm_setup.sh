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
chkconfig mongod on
service rabbitmq-server start
service mongod start
nohup splice-certmaker &

#function check_mongo() {
#    grep 'waiting for connections on port 27017' /var/log/mongodb/mongodb.log &> /dev/null
#    return $?
#}

# Ensure mongodb is up (sometimes it takes 30 seconds to finish it's first run)
#while [ check_mongo ]; do
#    echo "Waiting for mongodb to finish initialization"
#    sleep 1
#done

service splice_all restart


