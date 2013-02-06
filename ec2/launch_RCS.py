#!/usr/bin/env python
import os
import sys
from launch_instance import launch_instance, get_opt_parser, ssh_command, scp_to_command, run_command
from optparse import OptionParser

if __name__ == "__main__":
    default_product_data = None
    if os.environ.has_key("CLOUDE_GIT_REPO"):
        default_product_data = "%s/splice/sample-data/sample-certgen-products.json" % (os.environ["CLOUDE_GIT_REPO"])
    else:
        print "Couldn't find environment variable 'CLOUDE_GIT_REPO'"

    parser = OptionParser()
    parser.add_option('--product_data', action="store", default=default_product_data, 
            help="Product data for splice-certmaker: defaults to %s" % (default_product_data))
    parser = get_opt_parser(parser=parser)
    (opts, args) = parser.parse_args()
    instance = launch_instance(opts)
    hostname = instance.dns_name
    product_data = opts.product_data
    ssh_key = opts.ssh_key
    ssh_user = opts.ssh_user

    # open firewall
    print "Updating firewall rules"
    scp_to_command(hostname, ssh_user, ssh_key, "./etc/sysconfig/iptables", "/etc/sysconfig/iptables")
    ssh_command(hostname, ssh_user, ssh_key, "service iptables restart")

    # Run install script
    print "Running install script for RCS"
    scp_to_command(hostname, ssh_user, ssh_key, "./install_rpm_setup.sh", "~")
    ssh_command(hostname, ssh_user, ssh_key, "chmod +x ./install_rpm_setup.sh")
    ssh_command(hostname, ssh_user, ssh_key, "time ./install_rpm_setup.sh &> ./splice_install.log ")

    # Upload product data to cert-maker
    print "Uploading product_list data to splice-certmaker"
    cmd = "curl -X POST --data \"product_list=`cat %s`\"  http://%s:8080/productlist" % (product_data, hostname)
    run_command(cmd, retries=6, delay=5)
    print "RCS install completed on: %s" % (hostname)

