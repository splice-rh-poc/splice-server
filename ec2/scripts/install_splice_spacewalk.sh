if [ $# -lt 3 ]; then
    echo "Usage: $0 RHN_USER RHN_PASSWORD SATELLITE_CERT"
    exit 1
fi

RHN_USER=$1
RHN_PASS=$2
SAT_CERT=$3

# Look at what was used for /tmp/spacewalk.answers
SPACEWALK_DB=spaceschema
SPACEWALK_DB_USER=spaceuser
SPACEWALK_DB_PASS=spacepw

yum -y install postgresql-jdbc jmock git ant-nodeps ant-contrib junit ant-junit java-1.6.0-openjdk-devel checkstyle tito ant-apache-regexp spacewalk-pylint docbook-utils python-psycopg2
if [ ! -f /etc/yum/repos.d/oracle.repo ]; then
    cat > /etc/yum.repos.d/oracle.repo << EOF
[oracle]
name=Oracle
baseurl=http://ec2-23-22-86-129.compute-1.amazonaws.com/pub/oracle
enabled=1
gpgcheck=0
EOF
fi
yum -y install oracle-instantclient11.2-sqlplus oracle-instantclient11.2-basic oracle-lib-compat cx_Oracle

echo "Checkout Splice Spacewalk Git repo"
pushd .
git clone git://git.fedorahosted.org/git/spacewalk.git/
cd ~/spacewalk
git remote add spacewalk-splice https://github.com/splice/spacewalk.git
git fetch spacewalk-splice master:spacewalk-splice-master
git checkout spacewalk-splice-master
echo "Build & Install modified spacewalk/java RPM"
cd ~/spacewalk/java && tito build --test --rpm --install &> /root/spacewalk_java_rpm_build.log #this builds and installs spacewalk-java
if [ $? -ne 0 ]; then
    echo "Failed to build spacewalk/java"
    exit 1
fi
# Allows pgsql to run without a password
if [ ! -f ~/.pgpass ]; then
    echo "localhost:*:${SPACEWALK_DB}:${SPACEWALK_DB_USER}:${SPACEWALK_DB_PASS}" > ~/.pgpass
fi
chmod 600 ~/.pgpass
psql -U ${SPACEWALK_DB_USER} ${SPACEWALK_DB} -a -f /root/spacewalk/schema/spacewalk/upgrade/spacewalk-schema-1.8-to-spacewalk-schema-1.9/002-add_rhncpu_nrsocket.sql.postgresql
if [ $? -ne 0 ]; then
    echo "Unable to update schema"
    exit 1
fi
echo "Schema has been updated"
cd ~/spacewalk/backend && tito build --test --rpm --install &> /root/spacewalk_backend_rpm_build.log #this builds and installs spacewalk-backend
if [ $? -ne 0 ]; then
    echo "Failed to build spacewalk/backend"
    exit 1
fi
echo "spacewalk/backend RPM has been built & installed"
popd
service httpd restart
service tomcat6 restart
echo "Wait for tomcat6 to restart: `date`"
sleep 60
echo "Waited 60 seconds for tomcat6 to come up: `date`"

sed -i 's/^serverURL=.*/serverURL=https:\/\/xmlrpc.rhn.redhat.com\/XMLRPC/' /etc/sysconfig/rhn/up2date
sed -i 's/^sslCACert=.*/sslCACert=\/usr\/share\/rhn\/RHNS-CA-CERT/' /etc/sysconfig/rhn/up2date
rhnreg_ks --username ${RHN_USER} --password ${RHN_PASS}
if [ $? -ne 0 ]; then
    echo "Failed to register to RHN"
    exit 1
fi
echo "Registered to RHN, now will activate satellite: `date`"
sed -i 's/^server.satellite.rhn_parent.*/server.satellite.rhn_parent = satellite.rhn.redhat.com/' /etc/rhn/rhn.conf
rhn-satellite-activate --rhn-cert ${SAT_CERT} --ignore-version-mismatch
satellite-sync -c rhel-x86_64-server-6 --no-errata --no-kickstarts --no-packages --no-rpms
if [ $? -ne 0 ]; then
    echo "Failed to activate satellite"
    exit 1
fi
echo "Satellite has been activated: `date`"

