#!/bin/sh
source ./functions.sh

# Set hostname of instance to EC2 public hostname
HOSTNAME=`curl -s http://169.254.169.254/latest/meta-data/public-hostname`
hostname ${HOSTNAME}
sed -i "s/^HOSTNAME.*/HOSTNAME=${HOSTNAME}/" /etc/sysconfig/network

# Install EPEL
rpm -q epel-release &> /dev/null
if [ $? -eq 1 ]; then
    rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm || {
        echo "Unable to install EPEL"
        exit 1;
    }
fi


# FIXME: make quartz2-candlepin a dep of candlepin-tomcat6
yum install -y candlepin candlepin-tomcat6 liquibase quartz2-candlepin
echo "##Begin Splice Candlepin install script" >> /var/lib/pgsql/data/pg_hba.conf
echo "local   all       all                               trust" >> /var/lib/pgsql/data/pg_hba.conf
echo "host    all       all         127.0.0.1/32          trust" >> /var/lib/pgsql/data/pg_hba.conf
echo "##End Splice Candlepin install script" >> /var/lib/pgsql/data/pg_hba.conf
service postgresql restart
echo "Modified postgresql access and restarted service"
cp ~/context.xml /etc/tomcat6/context.xml
su - postgres -c 'createuser -dls candlepin'
/usr/share/candlepin/cpsetup
echo "Ran candlepin cpsetup will now restart tomcat6 and wait for tomcat6 to come up"
service tomcat6 restart

# Ensure candlepin is up
echo "Waiting 60 seconds to ensure tomcat6 is up: `date`"
sleep 60
echo "Assuming tomcat6 is up as of : `date`"
echo "Will begin curl commands"

curl -k -v -u admin:admin https://localhost:8443/candlepin/admin/init

cat > /root/owners.json << EOF
{
    "key": "admin",
    "displayName": "admin"
}
EOF

curl -k -H "content-type: application/json" -v -X POST -u admin:admin -d @/root/owners.json https://localhost:8443/candlepin/owners/

curl -k -H "Content-type: multipart/form-data" -u admin:admin -v -X POST -F import=@/root/manifest.zip "https://localhost:8443/candlepin/owners/admin/imports"

echo "Verify candlepin is functioning"
curl -k -u admin:admin https://localhost:8443/candlepin/pools
