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


import logging
import os
import sys

from datetime import date, datetime, timedelta

import mongoengine
from mongoengine.connection import register_connection

from splice.entitlement.models import SpliceServer, ConsumerIdentity,  ProductUsage
from rhic_serve.rhic_rest.models import RHIC

# os.environ['DJANGO_SETTINGS_MODULE'] = 'rhic_serve.settings'

logger = logging.getLogger(__name__)

MONGO_RCS_DATABASE_NAME = 'checkin_service'
mongoengine.connect(MONGO_RCS_DATABASE_NAME, alias=MONGO_RCS_DATABASE_NAME)
register_connection('default', MONGO_RCS_DATABASE_NAME)

MONGO_RHIC_DATABASE_NAME = 'rhic_serve'
mongoengine.connect(MONGO_RHIC_DATABASE_NAME, alias=MONGO_RHIC_DATABASE_NAME)

fact1 = {"memory_dot_memtotal": "604836", "lscpu_dot_cpu_socket(s)": "1"}
fact2 = {"memory_dot_memtotal": "1604836", "lscpu_dot_cpu_socket(s)": "4"}

facts = [fact1, fact2]

class ReportDataGenerator(object):

    def __init__(self):
        self.splice_servers = []
        self.rhics = []
        self.instance_identifiers = ['12:31:3D:08:40:%02d' % d for d in range(99)]

    def generate(self):
        self.create_splice_servers()
        self.create_rhics()
        self.create_usage()

    def create_splice_servers(self):
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
        s3, c = SpliceServer.objects.get_or_create(
                uuid='splice_server_uuid-3', 
                hostname='splice-server-3.spliceproject.org',
                environment='us-west-1', 
                description='Splice Server 3 in US East')

        self.splice_servers = [s1, s2, s3]

    def create_rhics(self):
        # shadowman@redhat.com
        r1, c = RHIC.objects.get_or_create(
                uuid='8d401b5e-2fa5-4cb6-be64-5f57386fda86',
                name='rhel-server-1190457-3116649-prem-l1-l3', 
                account_id='1190457',
                contract='3116649',
                support_level='prem', 
                sla='l1-l3',
                products=['RHEL Server',], 
                engineering_ids=[69,])
        r2, c = RHIC.objects.get_or_create(
                uuid='fea363f5-af37-4a23-a2fd-bea8d1fff9e8',
                name='rhel-server-jboss-1190457-3116649-prem-l1-l3', 
                account_id='1190457',
                contract='3116649', 
                support_level='prem', 
                sla='l1-l3',
                products=['RHEL Server', 'JBoss EAP'], 
                engineering_ids=[69, 183])
        r3, c = RHIC.objects.get_or_create(
                uuid='fbbd06c6-ebed-4892-87a3-2bf17c86e610',
                name='rhel-server-education-1190457-3879847-na-ss',
                account_id='1190457',
                contract='3116649', 
                support_level='ss', 
                sla='na',
                products=['RHEL Server for Education',],
                engineering_ids=[69])

        # slim@redhat.com
        r4, c = RHIC.objects.get_or_create(
                uuid='ee5c9aaa-a40c-4b58-80a6-ef731076bbe8',
                name='rhel-server-jboss-1238730-4582732-prem-l1-l3',
                account_id='3485301',
                contract='1238730', 
                support_level='prem', 
                sla='l1-l3',
                products=['RHEL Server', 'JBoss EAP'],
                engineering_ids=[69, 183])
        r5, c = RHIC.objects.get_or_create(
                uuid='b0e7bd8a-0b23-4b35-86d7-52a87311a5c2',
                name='openshift-gear-3485301-4582732-prem-l1-l3',
                account_id='3485301',
                contract='4582732', 
                support_level='prem', 
                sla='l1-l3',
                products=['OpenShift Gear',],
                engineering_ids=[69, 183])

        self.rhics = [r1, r2, r3, r4, r5]

    def create_usage(self):
        pass

def record_usage(identity, server, consumer_identifier, products, facts, date):


    prod_usage = ProductUsage(consumer=identity, splice_server=server,
        instance_identifier=consumer_identifier, product_info=products, facts=facts, date=date)
    #if not prod_usage:
    #    prod_usage = ProductUsage(consumer=identity, splice_server=server,
    #        instance_identifier=consumer_identifier, product_info=[])

    # Add this checkin's usage info
    #prod_usage.product_info.extend(prod_info)
    try:
        prod_usage.save()
    except Exception, e:
        logger.exception(e)
        print(e)
    return


def main():
    rdg = ReportDataGenerator()
    rdg.generate()


if __name__ == "__main__":
    main()
    sys.exit(0)

    start_date = "2012 01 01 05"
    end_date = "2012  01 07 05"
    
    startDate = datetime.strptime(start_date, "%Y %m %d %H")
    endDate = datetime.strptime(end_date, "%Y %m %d %H")
    currentDate = startDate
    delta=timedelta(hours=1)
    print('started', str(startDate), str(endDate))
    while currentDate < endDate:
        for c in consumers:
            for i in instance_identifier:
                #print(c, str(server1), i, ["69"], str(currentDate))
                record_usage(c, server1, i, ["69"], facts[0], currentDate )
            for i in instance_identifier:
                #print(c, str(server2), i, ["69", "83"], str(currentDate))
                record_usage(c, server2, i, ["69", "83"], facts[1], currentDate )
            for i in instance_identifier:
                #print(c, str(server2), i, ["69", "83"], str(currentDate))
                record_usage(c, server1, i, ["69", "183"], facts[1], currentDate )
            print('.')
        currentDate += delta


    print "Product Usage data has been written to mongo database '%s'" % (MONGO_DATABASE_NAME)
