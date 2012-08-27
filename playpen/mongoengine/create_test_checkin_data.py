#!/usr/bin/env python

import os
import sys
import time

from datetime import datetime
from mongoengine.document import Document

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
    uuid = "dummy_identifier value_%s" % (time.time())
    identity = ConsumerIdentity.objects(uuid=uuid).first()
    if not identity:
        identity = ConsumerIdentity(uuid=uuid, subscriptions=[])
        try:
            identity.save()
        except Exception, e:
            _LOG.exception(e)
    return identity

def create_marketing_products():
    # sample produts
# [(sku, product name), ...]

    p = [
    ('RH00001', 'Red Hat Enterprise Linux'),
    ('RH00002', 'Red Hat Enterprise Linux for Academia'),
    ('RH00003', 'Red Hat Enterprise Linux for Developers'),
    ('RH00004', 'Red Hat Enterprise MRG'),
    ('RH00005', 'Red Hat Enterprise High Availability'),
    ('RH00006', 'Red Hat Enterprise Load Balancing'),
    ('RH00007', 'Red Hat JBoss AS'),
    ('RH00008', 'Red Hat JBoss WS'),
    ('RH00009', 'Red Hat Database'),
    ('RH000010', 'Red Hat Cloudforms'),
    ]

    mps_list = []
    for i in p:
        mp = MarketingProduct(uuid=i[0], name=i[1], description=i[1])
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
    linux_marketing_products = MarketingProduct.objects(name__contains='Linux')
    jboss_marketing_products = MarketingProduct.objects(name__contains='JBoss')
    mrg_marketing_products = MarketingProduct.objects(name__contains='MRG')
    cf_marketing_products = MarketingProduct.objects(name__contains='Cloud')
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
