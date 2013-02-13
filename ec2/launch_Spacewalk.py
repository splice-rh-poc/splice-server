#!/usr/bin/env python
import os
import sys
import time
from launch_instance import launch_instance, get_opt_parser, ssh_command, scp_to_command, run_command, tag_instance
from optparse import OptionParser

if __name__ == "__main__":
    start = time.time()

    parser = OptionParser()
    parser = get_opt_parser(parser=parser)
    (opts, args) = parser.parse_args()
    instance = launch_instance(opts)
    hostname = instance.dns_name
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
    print "Running install script for Spacewalk"
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/functions.sh", "~")
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/install_spacewalk.sh", "~")

    # <- note spacewalk installer doesn't like this answer file in "~", it's unable to expand the "~" 
    # and results in no answer file being found
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/spacewalk.answers", "/tmp/") 
    ssh_command(hostname, ssh_user, ssh_key, "chmod +x ./install_spacewalk.sh")
    ssh_command(hostname, ssh_user, ssh_key, "time ./install_spacewalk.sh &> ./spacewalk_rpm_setup.log ")
    #
    # Update EC2 tag with version of RCS installed
    #
    print "Update EC2 tag with RPM version of 'spacewalk' installed on %s" % (hostname)
    rpm_ver = tag_instance(instance, hostname, ssh_user, ssh_key, "spacewalk-postgresql")

    end = time.time()
    print "Spacewalk %s install completed on: %s in %s seconds" % (rpm_ver, hostname, end-start)

