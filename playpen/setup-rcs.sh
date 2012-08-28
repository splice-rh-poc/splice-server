HOSTNAME=$1

setenforce 0
sed -i 's/enforcing/permissive/' /etc/selinux/config 
su -c 'rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm'
wget http://jmatthews.fedorapeople.org/splice.repo -O /etc/yum.repos.d/splice.repo
yum install -y splice

yum install -y python-pip
pip-python install django django-tastypie mongoengine django-tastypie-mongoengine

hostname $HOSTNAME
sed -i s/localhost.localdomain/$HOSTNAME/ /etc/sysconfig/network

yum install -y git
git clone https://github.com/splice/splice-server.git 
cd splice-server/playpen/certs
./setup.sh

service mongod restart
service httpd restart
