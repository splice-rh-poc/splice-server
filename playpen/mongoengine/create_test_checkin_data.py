#!/usr/bin/env python

import os
import sys
from datetime import date, datetime, timedelta
import datetime
from mongoengine.document import Document
import pycurl, cStringIO, json


MONGO_DATABASE_NAME = 'checkin_service'
import mongoengine
mongoengine.connect(MONGO_DATABASE_NAME)

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../../src/splice"))

from entitlement.models import SpliceServer, \
    ConsumerIdentity,  ProductUsage

import logging
_LOG = logging.getLogger(__name__)

# use real rhics from rhic_serve
consumers = [
             "5e6a8a78-ceb9-4835-80c8-4b2b337ebec4",
             "766fbcfb-3769-41f6-8034-e8c77737b3db",
             "2b8ef0ae-f6f4-45be-9d86-deb97a79d181",
             
             ]

instance_identifier = [
                       "12:31:3D:08:40:51",
                       "12:31:3D:08:40:52",
                       "12:31:3D:08:40:53",
                       #"12:31:3D:08:40:54",
                       #"12:31:3D:08:40:55",
                       #"12:31:3D:08:40:56",
                       #"12:31:3D:08:40:57",
                       #"12:31:3D:08:40:58",
                       #"12:31:3D:08:40:59",
                       #"12:31:3D:08:40:50",
                       ]


products = [
    ( [69], 'RHEL Server'),
    ( [83],  'RHEL HA'),
    ( [70], 'RHEL EUS'),
    ( [85], 'RHEL LB'),
    ( [183],  'JBoss EAP'),
    ([69], 'RHEL Server for Education')
    ]

fact1 = {"memory_dot_memtotal": "604836", "lscpu_dot_cpu_socket(s)": "1"}
fact2 = {"memory_dot_memtotal": "1604836", "lscpu_dot_cpu_socket(s)": "4"}

facts = [fact1, fact2]

def create_splice_server(switch=True):
    if switch:
        uuid="splice_server_1"
        hostname="splice_1"
        description="1"
    else:
        uuid="splice_server_2"
        hostname="splice_2"
        description="2"
    server = SpliceServer.objects(uuid=uuid).first()
    if not server:
        server = SpliceServer(uuid=uuid, description=description, hostname=hostname)
        try:
            server.save()
        except Exception, e:
            _LOG.exception(e)
    return server



   



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
        _LOG.exception(e)
        print(e)
    return


if __name__ == "__main__":
    server1 = create_splice_server(True)
    server2 = create_splice_server(False)
    start_date = "2012 01 01 05"
    end_date = "2012  01 07 05"
    
    startDate = datetime.datetime.strptime(start_date, "%Y %m %d %H")
    endDate = datetime.datetime.strptime(end_date, "%Y %m %d %H")
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
