#!/usr/bin/env python

import os
import sys
import time

from datetime import datetime

MONGO_DATABASE_NAME = 'checkin_service'
import mongoengine
mongoengine.connect(MONGO_DATABASE_NAME)

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../../checkin_service/src"))

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
    mp1_id = "dummy_value_1"
    mp1_name = "dummy_value_name_1"
    mp1_description = "dummy_value_description_1"
    mp2_id = "dummy_value_2"
    mp2_name = "dummy_value_name_2"
    mp2_description = "dummy_value_descripion_2"

    mp1 = MarketingProduct.objects(uuid=mp1_id, name=mp1_name, description=mp1_description).first()
    if not mp1:
        mp1 = MarketingProduct(uuid=mp1_id, name=mp1_name, description=mp1_description)
        try:
            mp1.save()
        except Exception,e:
            _LOG.exception(e)
    mp2 = MarketingProduct.objects(uuid=mp2_id, name=mp2_name, description=mp2_description).first()
    if not mp2:
        mp2 = MarketingProduct(uuid=mp2_id, name=mp2_name, description=mp2_description)
        try:
            mp2.save()
        except Exception, e:
            _LOG.exception(e)
    return [mp1, mp2]

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
    marketing_products = create_marketing_products()
    print "Created marketing products: %s" % (marketing_products)

    for index in range(0,5):
        record_usage(server, identity, "MAC_ADDR_1", marketing_products)
        record_usage(server, identity, "MAC_ADDR_2", marketing_products)
    print "Product Usage data has been written to mongo database '%s'" % (MONGO_DATABASE_NAME)
