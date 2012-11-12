#!/usr/bin/env python

import json
import logging
import logging.config
import os

from datetime import datetime
from dateutil.tz import tzutc


from mongoengine.connection import connect, disconnect
from splice.entitlement.models import ProductUsage

DB_NAME = "test_product_usage"
DB_CONN = None

LOG_CONFIG_FILE=os.path.join(os.path.abspath(os.path.dirname(__file__)), "logging_config")
logging.config.fileConfig(LOG_CONFIG_FILE)
_LOG = logging.getLogger(__name__)


class MongoEncoder(json.JSONEncoder):
    def default(self, obj, **kwargs):
        from pymongo.objectid import ObjectId
        import mongoengine
        import types
        if isinstance(obj, (mongoengine.Document, mongoengine.EmbeddedDocument)):
            out = dict(obj._data)
            for k,v in out.items():
                if isinstance(v, ObjectId):
                    _LOG.info("k = %s, v = %s" % (k,v))
                    out[k] = str(v)
            return out
        elif isinstance(obj, mongoengine.queryset.QuerySet):
            return list(obj)
        elif isinstance(obj, types.ModuleType):
            return None
        elif isinstance(obj, (list,dict)):
            return obj
        elif isinstance(obj, datetime):
            return str(obj)
        else:
            return JSONEncoder.default(obj, **kwargs)

def clean():
    return
    global DB_CONN
    if not DB_CONN:
        DB_CONN = connect(DB_NAME)
    DB_CONN.drop_database(DB_NAME)

def init():
    global DB_CONN
    clean()
    DB_CONN = connect(DB_NAME)

def get_product_usage():
    pu = ProductUsage()
    pu.consumer = "fb647f68-aa01-4171-b62b-35c2984a5328"
    pu.splice_server = "aa111a11-aa01-1111-a00a-00a1111a1111"
    pu.instance_identifier = "A0:A0:A0:A0:00:A0"
    pu.allowed_product_info = ["1", "2", "3"]
    pu.unallowed_product_info = ["100", "200"]
    pu.facts = {"tbd": "values"}
    pu.date = datetime.now(tzutc())
    pu.save()
    obj = ProductUsage.objects()
    return obj[0]

def to_json(obj):
    return json.dumps(obj, cls=MongoEncoder, indent=2)

if __name__ == "__main__":
    _LOG.info("test")
    init()
    pu = get_product_usage()
    pu_json = to_json(pu)
    
    _LOG.info("Original: %s\n translated to JSON = \n%s" % (pu, pu_json))
    clean()

