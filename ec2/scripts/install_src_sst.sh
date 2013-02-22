#deps for building python-rhsm
yum -y install gcc openssl-devel

echo "Checkout python-rhsm repo"
pushd .
git clone git://github.com/splice/python-rhsm.git
cd ~/python-rhsm
git checkout -b checkin
git reset --hard origin/checkin
echo "Build & Install modified python-rhsm RPM"
cd ~/python-rhsm && tito build --test --rpm --install &> /root/python-rhsm_rpm_build.log #this builds and installs python-rhsm
if [ $? -ne 0 ]; then
    echo "Failed to build python-rhsm"
    exit 1
fi
echo "python-rhsm RPM has been built & installed"


if [ ! -f /etc/yum/repos.d/splice.repo ]; then
    cat > /etc/yum.repos.d/splice.repo << EOF
[splice]
name=splice
baseurl=http://ec2-23-22-86-129.compute-1.amazonaws.com/pub/el6/x86_64
enabled=1
gpgcheck=0
EOF
fi

popd


# install base sst before checking out dev version
yum install -y spacewalk-splice-tool

echo "Checkout spacewalk-splice-tool repo"
pushd .
git clone git://github.com/splice/spacewalk-splice-tool.git
echo "Build & Install spacewalk-splice-tool RPM"
cd ~/spacewalk-splice-tool && tito build --test --rpm --install &> /root/sst_rpm_build.log
if [ $? -ne 0 ]; then
    echo "Failed to build spacewalk-splice-tool"
    exit 1
fi
echo "spacewalk-splice-tool RPM has been built & installed"
