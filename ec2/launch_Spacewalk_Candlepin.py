#!/usr/bin/env python
import os
import sys
import time
from datetime import datetime
from launch_instance import launch_instance, get_opt_parser, ssh_command, scp_to_command, run_command, tag_instance
from optparse import OptionParser

if __name__ == "__main__":
    start = time.time()
    
    default_sat_cert = None
    if os.environ.has_key("CLOUDE_GIT_REPO"):
        default_sat_cert = "%s/splice/certs/internal-satellite-cert.xml" % (os.environ["CLOUDE_GIT_REPO"])
        if not os.path.isfile(default_sat_cert):
            print "Warning: Satellite Certificate not found at: %s" % (default_sat_cert)
            print "Unable to set default value"
            default_sat_cert = None
    else:
        print "Couldn't find environment variable 'CLOUDE_GIT_REPO'"

    parser = OptionParser()
    parser = get_opt_parser(parser=parser)
    parser.add_option('--manifest', action="store", default=None, help="Subscription Manifest to load into Candlepin")
    parser.add_option('--rhn_user', action="store", default=None, help="RHN Username to activate Satellite with")
    parser.add_option('--rhn_pass', action="store", default=None, help="RHN Password to activate Satellite with")
    parser.add_option('--sat_cert', action="store", default=default_sat_cert, help="Satellite Certificate")
    
    (opts, args) = parser.parse_args()
    manifest = opts.manifest
    if not manifest or not os.path.isfile(opts.manifest):
        print "Please re-run with '--manifest' point to a subscription manifest file"
        sys.exit(1)
    if not opts.rhn_user or not opts.rhn_pass:
        print "Please re-run with '--rhn_user', '--rhn_pass'"
        sys.exit(1)
    if not opts.sat_cert:
        print "Please re-run with '--sat_cert' pointing to a valid Satellite certificate"
        sys.exit(1)
    instance = launch_instance(opts)
    print "Instance %s is up: %s" % (instance.dns_name, datetime.now())
    hostname = instance.dns_name
    ssh_key = opts.ssh_key
    ssh_user = opts.ssh_user
    rhn_user = opts.rhn_user
    rhn_pass = opts.rhn_pass
    sat_cert = opts.sat_cert
    #
    # open firewall
    #
    print "Updating firewall rules"
    scp_to_command(hostname, ssh_user, ssh_key, "./etc/sysconfig/iptables", "/etc/sysconfig/iptables")
    ssh_command(hostname, ssh_user, ssh_key, "service iptables restart")
    #
    # Run install script
    #
    print "Running install script for Spacewalk: %s" % (datetime.now())
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/functions.sh", "~")
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/install_spacewalk.sh", "~")
    # <- note spacewalk installer doesn't like this answer file in "~", it's unable to expand the "~" 
    # and results in no answer file being found
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/spacewalk.answers", "/tmp/") 
    ssh_command(hostname, ssh_user, ssh_key, "chmod +x ./install_spacewalk.sh")
    ssh_command(hostname, ssh_user, ssh_key, "time ./install_spacewalk.sh &> ./spacewalk_rpm_setup.log ")

    # Begin CandlePin Install
    print "Beginning Candlepin Install: %s" % (datetime.now())
    scp_to_command(hostname, ssh_user, ssh_key, opts.manifest, "~/manifest.zip")
    # ssh_command(hostname, ssh_user, ssh_key, "mv %s manifest.zip" % os.path.basename(opts.manifest))
    scp_to_command(hostname, ssh_user, ssh_key, "./etc/tomcat/context.xml", "~/context.xml")
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/install_candlepin.sh", "~") 
    ssh_command(hostname, ssh_user, ssh_key, "chmod +x ./install_candlepin.sh")
    ssh_command(hostname, ssh_user, ssh_key, "time ./install_candlepin.sh &> ./candlepin_rpm_setup.log ")

    # Begin Splice Spacewalk Modifed install
    print "Building modified Splice Spacewalk RPMs: %s" % (datetime.now())
    scp_to_command(hostname, ssh_user, ssh_key, opts.sat_cert, "~/satellite_cert.xml")
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/install_splice_spacewalk.sh", "~") 
    ssh_command(hostname, ssh_user, ssh_key, "chmod +x ./install_splice_spacewalk.sh")
    cmd = "time ./install_splice_spacewalk.sh %s %s %s &> ./splice_spacewalk_setup.log" % (opts.rhn_user, opts.rhn_pass, "~/satellite_cert.xml")
    ssh_command(hostname, ssh_user, ssh_key, cmd)
    # Begin Candlepin Modifed install
    print "Building modified Candlepin RPMs: %s" % (datetime.now())
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/install_src_candlepin.sh", "~") 
    ssh_command(hostname, ssh_user, ssh_key, "chmod +x ./install_src_candlepin.sh")
    cmd = "time ./install_src_candlepin.sh &> ./src_candlepin_setup.log"
    ssh_command(hostname, ssh_user, ssh_key, cmd)
    # Begin python-rhsm install
    print "Building modified python-rhsm and spacewalk-splice-tool RPMs: %s" % (datetime.now())
    scp_to_command(hostname, ssh_user, ssh_key, "./scripts/install_src_sst.sh", "~") 
    ssh_command(hostname, ssh_user, ssh_key, "chmod +x ./install_src_sst.sh")
    cmd = "time ./install_src_sst.sh &> ./src_sst.log"
    ssh_command(hostname, ssh_user, ssh_key, cmd)
    #
    # Update EC2 tag with version of RCS installed
    #
    print "Update EC2 tag with RPM version of 'spacewalk' installed on %s" % (hostname)
    rpm_ver = tag_instance(instance, hostname, ssh_user, ssh_key, "spacewalk-postgresql", "spacewalk-candlepin")

    end = time.time()
    print "Spacewalk %s install completed on: %s in %s seconds" % (rpm_ver, hostname, end-start)

