#!/usr/bin/env python

import os
import sys
import time

from datetime import datetime
from mongoengine.document import Document
import pycurl, cStringIO, json


MONGO_DATABASE_NAME = 'checkin_service'
import mongoengine
mongoengine.connect(MONGO_DATABASE_NAME)

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../../src/splice"))

from entitlement.models import SpliceServer, MarketingProduct, \
    ConsumerIdentity, ReportingItem, ProductUsage

import logging
_LOG = logging.getLogger(__name__)

def create_splice_server():
    uuid="splice_server_1"
    server = SpliceServer.objects(uuid=uuid).first()
    if not server:
        server = SpliceServer(uuid=uuid, description="Test data", hostname="somewhere.example.com:8000")
        try:
            server.save()
        except Exception, e:
            _LOG.exception(e)
    return server


def create_consumer_identity():
    
    buf = cStringIO.StringIO()
    URL = 'http://ec2-184-72-159-16.compute-1.amazonaws.com:8000/api/account/'
    USER = 'shadowman@redhat.com'
    PASS = 'shadowman@redhat.com'
    conn = pycurl.Curl()
    conn.setopt(pycurl.USERPWD, "%s:%s" % (USER, PASS))
    conn.setopt(pycurl.URL, URL)
    conn.setopt(pycurl.WRITEFUNCTION, buf.write)
    conn.perform()
    
    data = json.loads(buf.getvalue())
    #consumer = data[0]['account_id'].encode('ascii')
    consumer =  data[0]['resource_uri'].encode('ascii').split('/')[-2]
    
    
    identity = ConsumerIdentity(uuid=consumer, subscriptions=[])
    try:
        identity.save()
    except Exception, e:
        _LOG.exception(e)
    return identity
    
    '''
    uuid = "dummy_identifier value_%s" % (time.time())
    identity = ConsumerIdentity.objects(uuid=uuid).first()
    if not identity:
        identity = ConsumerIdentity(uuid=uuid, subscriptions=[])
        try:
            identity.save()
        except Exception, e:
            _LOG.exception(e)
    return identity
    '''
    
def create_marketing_products():
    # sample produts
# [(sku, product name), ...]

    p = [
    ('RH00001', 69, 'RHEL Server'),
    ('RH00002', 83,  'RHEL HA'),
    ('RH00003', 70, 'RHEL EUS'),
    ('RH00004', 85, 'RHEL LB'),
    ('RH00005', 183,  'JBoss EAP'),
    ('RH00006', 69, 'RHEL Server for Education'),
    ]

    mps_list = []
    for i in p:
        mp = MarketingProduct(uuid=i[0], engineering_id = i[1], name=i[2], description=i[2])
        mp.tags = ['mongodb', 'mongoengine']
        mp.save()

def record_usage(server, identity, consumer_identifier, marketing_products):
    prod_info = []
    for mp in marketing_products:
        prod_info.append(ReportingItem(product=mp, date=datetime.now()))

    prod_usage = ProductUsage.objects(consumer=identity, splice_server=server,
        instance_identifier=consumer_identifier).first()
    if not prod_usage:
        prod_usage = ProductUsage(consumer=identity, splice_server=server,
            instance_identifier=consumer_identifier, product_info=[])

    # Add this checkin's usage info
    prod_usage.product_info.extend(prod_info)
    try:
        prod_usage.save()
    except Exception, e:
        _LOG.exception(e)
    return


if __name__ == "__main__":
    server = create_splice_server()
    identity = create_consumer_identity()
    print "Created consumer identity: %s  <%s>" % (identity.uuid, identity)
    create_marketing_products()
    linux_marketing_products = MarketingProduct.objects(name__contains='RHEL')
    jboss_marketing_products = MarketingProduct.objects(name__contains='JBoss')
    mrg_marketing_products = MarketingProduct.objects(name__contains='EUS')
    cf_marketing_products = MarketingProduct.objects(name__contains='HA')
    print "Created marketing products: %s" % (linux_marketing_products)
    print "Created marketing products: %s" % (jboss_marketing_products)

    for index in range(0,9):
        record_usage(server, identity, "MAC_ADDR_1", linux_marketing_products)
    for index in range(0,7):
        record_usage(server, identity, "MAC_ADDR_2", linux_marketing_products)
    for index in range(0,5):
        record_usage(server, identity, "MAC_ADDR_1", jboss_marketing_products)
    for index in range(0,3):
        record_usage(server, identity, "MAC_ADDR_2", mrg_marketing_products)
    for index in range(0,1):
        record_usage(server, identity, "MAC_ADDR_2", cf_marketing_products)
    print "Product Usage data has been written to mongo database '%s'" % (MONGO_DATABASE_NAME)
