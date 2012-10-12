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

yum install splice || {
    echo "yum install of splice failed"
    exit 1;
}
