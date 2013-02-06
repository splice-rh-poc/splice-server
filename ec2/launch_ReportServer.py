#!/usr/bin/env python
import sys
import time
from launch_instance import launch_instance, get_opt_parser, ssh_command, scp_to_command, run_command
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
    print "Running install script for ReportServer"
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/functions.sh", "~")
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/install_rpm_setup.sh", "~")
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/install_report_server.sh", "~")
    ssh_command(hostname, ssh_user, ssh_key, "chmod +x ./*.sh")
    ssh_command(hostname, ssh_user, ssh_key, "time ./install_rpm_setup.sh &> ./splice_rpm_setup.log ")
    ssh_command(hostname, ssh_user, ssh_key, "time ./install_report_server.sh &> ./splice_report_server_install.log ")
    #
    # Update EC2 tag with version of RCS installed
    #
    print "Update EC2 tag with RPM version of 'report-server' installed on %s" % (hostname)
    status, out, err = ssh_command(hostname, ssh_user, ssh_key, "rpm -q --queryformat \"%{VERSION}\" report-server")
    rs_ver = out
    tag = ""
    if instance.__dict__.has_key("tags"):
        all_tags = instance.__dict__["tags"]
        if all_tags.has_key("Name"):
            tag = all_tags["Name"]
    if not tag:
        import getpass
        tag = "%s %s" % (getpass.getuser(), hostname)
    tag += " ReportServer %s" % (rs_ver)
    instance.add_tag("Name","%s" % (tag))

    end = time.time()
    print "ReportServer %s install completed on: %s in %s seconds" % (rs_ver, hostname, end-start)
    print "Visit https://%s/report-server/ui20" % (hostname)
