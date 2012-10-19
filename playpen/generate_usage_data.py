#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""
Generates RHIC usage date on a splice server.
"""

from datetime import date, datetime, timedelta
from optparse import OptionParser
import logging
import os
import sys

import isodate

from mongoengine.connection import register_connection
import mongoengine

from splice.common.models import SpliceServer, ConsumerIdentity,  ProductUsage
from rhic_serve.rhic_rest.models import RHIC


# Logging config
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# DB Setup
# We need to connect to the checkin_service db and the rhic_serve db since
# RHIC's live in rhic_serve.
MONGO_RCS_DATABASE_NAME = 'checkin_service'
mongoengine.connect(MONGO_RCS_DATABASE_NAME, alias=MONGO_RCS_DATABASE_NAME)
register_connection('default', MONGO_RCS_DATABASE_NAME)
MONGO_RHIC_DATABASE_NAME = 'rhic_serve'
mongoengine.connect(MONGO_RHIC_DATABASE_NAME, alias=MONGO_RHIC_DATABASE_NAME)

# Facts for instances
fact1 = {"memory_dot_memtotal": "604836", "lscpu_dot_cpu_socket(s)": "1", "lscpu_dot_cpu(s)": "1"}
fact2 = {"memory_dot_memtotal": "9048360", "lscpu_dot_cpu_socket(s)": "2", "lscpu_dot_cpu(s)": "2"}
fact3 = {"memory_dot_memtotal": "16048360", "lscpu_dot_cpu_socket(s)": "4", "lscpu_dot_cpu(s)": "4"}
facts = [fact1, fact2, fact3]

# Each mac address pattern below will be used by the
# instances assigned to 1 rhic.
#
# Since the pattern only allows for the last 2 digits of the mac address to be
# used by the RHIC to generate unique mac addresses, this limits
# each rhic to 100 instances.  We can change this if needed.
mac_addr_patterns = [
    '12:31:3D:08:40:%02d',
    '12:31:3D:08:41:%02d',
    '12:31:3D:08:42:%02d',
    '12:31:3D:08:43:%02d',
    '12:31:3D:08:44:%02d',
    '12:31:3D:08:45:%02d',
    '12:31:3D:08:46:%02d',
    '12:31:3D:08:47:%02d',
    '12:31:3D:08:48:%02d',
    '12:31:3D:08:49:%02d',]

# Start and End defaults, these can be overriden via command line parameters.
# The defualt is 3 months of data, July, August, and September of 2012.
START_DATETIME = '20120701T00:00Z'
END_DATETIME = '20120930T00:00Z'

class RHICData(object):
    """
    RHIC represenation. Encompasses a RHIC model, the number of instances using
    that RHIC, instance identifiers (mac addresses) and instance facts.
    """
    def __init__(self, num_instances, **fields):
        self.num_instances = num_instances
        # Grab a mac address pattern
        self.mac_addr_pattern = mac_addr_patterns.pop()
        # Generate one mac addresse per instance
        self.instance_identifiers = ['12:31:3D:08:40:%02d' % d for d in
                                      range(self.num_instances)]
        # Generate a set of facts per instance.  This just picks facts 
        # from the list of facts via round-robin.
        self.instance_facts = [facts[d % len(facts)] for d in 
                               range(self.num_instances)]

        # Save the RHIC model.
        self.rhic_model, created = RHIC.objects.get_or_create(**fields)

        # Make the model fields easier to access directly on this instance.
        for k, v in fields.items():
            setattr(self, k, v)


class ReportDataGenerator(object):
    """
    Report data generator class.

    1. Generates RHICS
    2. Generates Splice Servers
    3. Generates product usage for RHICS
    """

    def __init__(self, start_datetime, end_datetime, num_instances):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.interval = timedelta(hours=1)
        self.num_instances = num_instances
        self.splice_servers = []
        self.rhics = []

    def generate(self):
        """
        Generate all the data.
        """
        self.generate_splice_servers()
        self.generate_rhics()
        num_generated = self.generate_usage()
        return num_generated

    def generate_splice_servers(self):
        """
        Generate Splice Servers.
        """
        # 2 servers in us-east-1
        s1, c = SpliceServer.objects.get_or_create(
            uuid='splice_server_uuid-1', 
            hostname='splice-server-1.spliceproject.org',
            environment='us-east-1', 
            description='Splice Server 1 in US East')
        s2, c = SpliceServer.objects.get_or_create(
            uuid='splice_server_uuid-2', 
            hostname='splice-server-2.spliceproject.org',
            environment='us-east-1', 
            description='Splice Server 2 in US East')
        # 1 server in us-west-1
        s3, c = SpliceServer.objects.get_or_create(
            uuid='splice_server_uuid-3', 
            hostname='splice-server-3.spliceproject.org',
            environment='us-west-1', 
            description='Splice Server 3 in US East')

        self.splice_servers = [s1, s2, s3]

    def generate_rhics(self):
        """
        Generate RHIC's.

        Each RHIC is associated with self.num_instances instances.  This value
        can be changed in the instantiation of RHICData.
        """
        # RHIC's for login: shadowman@redhat.com
        #
        # Premium RHEL Server
        r1 = RHICData(
            num_instances=self.num_instances,
            uuid='8d401b5e-2fa5-4cb6-be64-5f57386fda86',
            name='rhel-server-1190457-3116649-prem-l1-l3', 
            account_id='1190457',
            contract='3116649',
            support_level='l1-l3', 
            sla='prem',
            products=['RHEL Server',], 
            engineering_ids=['69',])
        # Premium RHEL Server and JBoss
        r2 = RHICData(
            num_instances=self.num_instances,
            uuid='fea363f5-af37-4a23-a2fd-bea8d1fff9e8',
            name='rhel-server-jboss-1190457-3116649-prem-l1-l3', 
            account_id='1190457',
            contract='3116649', 
            support_level='l1-l3', 
            sla='prem',
            products=['RHEL Server', 'JBoss EAP'], 
            engineering_ids=['69', '183'])
        # Self Support RHEL Server for Education
        r3 = RHICData(
            num_instances=self.num_instances,
            uuid='fbbd06c6-ebed-4892-87a3-2bf17c86e610',
            name='rhel-server-education-1190457-3879847-na-ss',
            account_id='1190457',
            contract='3879847', 
            support_level='ss', 
            sla='na',
            products=['RHEL Server for Education'],
            engineering_ids=['69'])
        
        r4 = RHICData(
            num_instances=self.num_instances,
            uuid='fbbd06c6-ebed-4892-87a3-2bf17c864444',
            name='rhel-ha-1190457-3874444-na-standard',
            account_id='1190457',
            contract='3116649', 
            support_level='l1-l3', 
            sla='prem',
            products=['RHEL HA',],
            engineering_ids=['83'])

        # RHIC's for login: slim@redhat.com
        #
        # Premium RHEL Server and JBoss
        r5 = RHICData(
            num_instances=self.num_instances,
            uuid='ee5c9aaa-a40c-1111-80a6-ef731076bbe8',
            name='jboss-1111730-4582732-prem-l1-l3',
            account_id='1190480',
            contract='3879880', 
            support_level='l3', 
            sla='std',
            products=['JBoss EAP'],
            engineering_ids=['183'])
        # Premium OpenShift Gear (encompasses RHEL Server and JBoss Engineering
        # Id's).
        r6 = RHICData(
            num_instances=self.num_instances,
            uuid='b0e7bd8a-0b23-4b35-86d7-52a87311a5c2',
            name='openshift-gear-3485301-4582732-prem-l1-l3',
            account_id='3485301',
            contract='4582732', 
            support_level='l1-l3', 
            sla='prem',
            products=['OpenShift Gear',],
            engineering_ids=['69', '183'])
        
        r7 = RHICData(
            num_instances=self.num_instances,
            uuid='fbbd06c6-ebed-4892-87a3-2bf17c865555',
            name='rhel-eus-1190457-3874444-prem-l1-l3',
            account_id='3485301',
            contract='1238730', 
            support_level='l1-l3', 
            sla='prem',
            products=['RHEL EUS',],
            engineering_ids=['70'])
        
        r8 = RHICData(
            num_instances=self.num_instances,
            uuid='fbbd06c6-ebed-4892-87a3-2bf17c866666',
            name='rhel-lb-1190457-3874444-prem-l1-l3',
            account_id='3485301',
            contract='1238730', 
            support_level='l3', 
            sla='prem',
            products=['RHEL LB',],
            engineering_ids=['85'])
        
        r9 = RHICData(
            num_instances=self.num_instances,
            uuid='fbbd06c6-ebed-4892-87a3-2bf17c867777',
            name='rhel-2socket_unlimited-1190457-3874444-prem-l1-l3',
            account_id='3485301',
            contract='1238730', 
            support_level='l1-l3', 
            sla='prem',
            products=['RHEL Server 2-socket Unlimited Guest'],
            engineering_ids=['69'])

        self.rhics = [r1, r2, r3, r4, r5, r6, r7, r8, r9]

    def generate_usage(self):
        """
        Generate actual usage.

        The basic pattern is:
        For each hour between start and end time:
            For each rhic:
                For each instance associated with the rhic:
                    Record Product Usage for the instance
        """
        # Generate usage for each RHIC
        num_generated = 0
        usage_datetime = self.start_datetime
        while usage_datetime < self.end_datetime:
            if usage_datetime.hour % 24 == 0:
                logger.info('Generating data for %s' % usage_datetime)
                logger.info('%s records generated so far' % num_generated)
            for rhic in self.rhics:
                # Generate usage for each instance associated with the RHIC.
                for inst_index in range(rhic.num_instances):
                    # TODO: figure out how we want to distribute across splice
                    # servers
                    splice_server = self.splice_servers[0]
                    self.record_rhic_usage(rhic, inst_index, usage_datetime,
                                           splice_server.uuid)
                    num_generated += 1
            usage_datetime += self.interval

        return num_generated

    def record_rhic_usage(self, rhic, inst_index, usage_datetime, 
                          splice_server):
        """
        Record one record of a RHIC usage.
        """
        pu = ProductUsage(
            consumer=rhic.uuid, splice_server=splice_server,
            instance_identifier=rhic.instance_identifiers[inst_index], 
            allowed_product_info=rhic.engineering_ids,
            facts=rhic.instance_facts[inst_index], date=usage_datetime)
        pu.save()
            

def clear_product_usage():
    """
    Clear all product usage from the db.
    """
    logger.info('Clearing product usage from the db.')
    ProductUsage.objects.delete()


def main(start_datetime, end_datetime, num_instances):
    start_datetime = isodate.parse_datetime(start_datetime)
    end_datetime = isodate.parse_datetime(end_datetime)
    rdg = ReportDataGenerator(start_datetime, end_datetime, num_instances)
    return rdg.generate()



if __name__ == "__main__":
    
    parser = OptionParser()
    parser.add_option('-c', '--clear', dest='clear', action='store_true',
                      help=('clear all product usage from the db before '
                           'generation.'))
    parser.add_option('-n', '--num-instances', dest='num_instances', 
                      action='store', default=20, type='int',
                      help=('number of instances to associate with each rhic '
                            'generated [default: %default]'))
    parser.add_option('-s', '--start-datetime', dest='start_datetime',
                      action='store', default=START_DATETIME,
                      help=('start date and time in iso8601 format that will '
                            'be used for usage generation '
                            '[default: %default]'))
    parser.add_option('-e', '--end-datetime', dest='end_datetime',
                      action='store', default=END_DATETIME,
                      help=('end date and time in iso8601 format that will '
                            'be used for usage generation '
                            '[default: %default]'))
    options, args = parser.parse_args()

    if options.clear:
        clear_product_usage()

    num_generated = main(options.start_datetime,
                         options.end_datetime,
                         options.num_instances)

    logger.info('Product Usage data has been written to mongo database %s' %
        MONGO_RCS_DATABASE_NAME)
    logger.info('%s total records generated.' % num_generated)
    sys.exit(0)
