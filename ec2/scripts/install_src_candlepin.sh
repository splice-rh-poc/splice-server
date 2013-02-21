#deps for building candlepin
yum -y install hardlink selinux-policy-doc

echo "Checkout Splice Candlepin Git repo"
pushd .
git clone git://github.com/beav/candlepin.git
cd ~/candlepin
git checkout -b buildtest
git reset --hard origin/buildtest
echo "Build & Install modified candlepin RPM"
cd ~/candlepin && tito build --test --rpm --install &> /root/candlepin_rpm_build.log #this builds and installs candlepin
if [ $? -ne 0 ]; then
    echo "Failed to build candlepin"
    exit 1
fi
echo "candlepin RPM has been built & installed"
echo "update candlepin schema"
/usr/share/candlepin/cpdb --update
if [ $? -ne 0 ]; then
    echo "Failed to update candlepin schema"
fi
echo "update candlepin schema successful"
popd
service tomcat6 restart
echo "Wait for tomcat6 to restart: `date`"
sleep 60
echo "Waited 60 seconds for tomcat6 to come up: `date`"

