#!/usr/bin/env python
import os
import sys
import time
from launch_instance import launch_instance, get_opt_parser, ssh_command, scp_to_command, run_command
from optparse import OptionParser

if __name__ == "__main__":
    start = time.time()
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
    #
    # open firewall
    #
    print "Updating firewall rules"
    scp_to_command(hostname, ssh_user, ssh_key, "./etc/sysconfig/iptables", "/etc/sysconfig/iptables")
    ssh_command(hostname, ssh_user, ssh_key, "service iptables restart")
    #
    # Run install script
    #
    print "Running install script for RCS"
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/functions.sh", "~")
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/install_rpm_setup.sh", "~")
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/install_rcs.sh", "~")
    ssh_command(hostname, ssh_user, ssh_key, "chmod +x ./install_rpm_setup.sh")
    ssh_command(hostname, ssh_user, ssh_key, "time ./install_rpm_setup.sh &> ./splice_rpm_setup.log ")
    ssh_command(hostname, ssh_user, ssh_key, "time ./install_rcs.sh &> ./splice_rcs_install.log ")
    #
    # Upload product data to cert-maker
    #
    print "Uploading product_list data to splice-certmaker"
    cmd = "curl -X POST --data \"product_list=`cat %s`\"  http://%s:8080/productlist" % (product_data, hostname)
    run_command(cmd, retries=6, delay=5)
    #
    # Update EC2 tag with version of RCS installed
    #
    print "Update EC2 tag with RPM version of 'splice' installed on %s" % (hostname)
    status, out, err = ssh_command(hostname, ssh_user, ssh_key, "rpm -q --queryformat \"%{VERSION}\" splice")
    rcs_ver = out
    tag = ""
    if instance.__dict__.has_key("tags"):
        all_tags = instance.__dict__["tags"]
        if all_tags.has_key("Name"):
            tag = all_tags["Name"]
    if not tag:
        import getpass
        tag = "%s %s" % (getpass.getuser(), hostname)
    tag += " RCS %s" % (rcs_ver)
    instance.add_tag("Name","%s" % (tag))

    end = time.time()
    print "RCS %s install completed on: %s in %s seconds" % (rcs_ver, hostname, end-start)

