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

import json
import os
import time
import uuid

from datetime import timedelta
from datetime import datetime
from dateutil.tz import tzutc
import pytz

from logging import getLogger

from tastypie.test import ResourceTestCase

from mongoengine import Document, StringField
from mongoengine.connection import connect, disconnect
from mongoengine.queryset import QuerySet
from django.conf import settings

from certutils.certutils import CertUtils

from splice.common import candlepin_client
from splice.common import config
from splice.common import rhic_serve_client
from splice.common import utils
from splice.common.exceptions import UnsupportedDateFormatException, UnexpectedStatusCodeException, NotFoundConsumerIdentity
from splice.common.identity import create_or_update_consumer_identity, sync_from_rhic_serve, \
        sync_from_rhic_serve_blocking, SyncRHICServeThread
from splice.common.models import ConsumerIdentity, IdentitySyncInfo, RHICLookupTask, ProductUsage
from splice.entitlement.checkin import CheckIn
from splice.managers import identity_lookup

from splice.common import identity

TEST_DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..", "test_data")
LOG = getLogger(__name__)


# Adapted From:
# https://github.com/vandersonmota/mongoengine_django_tests/blob/master/mongotest.py
class MongoTestCase(ResourceTestCase):
    """
    TestCase class that clear the collection between the tests
    """
    #db_name = 'test_%s' % settings.MONGO_DATABASE_NAME
    db_name = settings.MONGO_DATABASE_NAME
    def __init__(self, methodName='runtest'):
        super(MongoTestCase, self).__init__(methodName)
        disconnect()
        self.db = connect(self.db_name)
        self.drop_database_and_reconnect()

    def _post_teardown(self):
        super(MongoTestCase, self)._post_teardown()
        self.drop_database_and_reconnect(reconnect=False)

    def drop_database_and_reconnect(self, reconnect=True):
        disconnect()
        self.db.drop_database(self.db_name)
        # Mongoengine sometimes doesn't recreate unique indexes
        # in between test runs, adding the below 'reset' to fix this
        # https://github.com/hmarr/mongoengine/issues/422
        QuerySet._reset_already_indexed()
        if reconnect:
            self.db = connect(self.db_name)



def mocked_candlepin_client_request_method(host, port, url, installed_product,
                                           identity, username, password,
                                           start_date=None, end_date=None, debug=False):
    example_data = os.path.join(TEST_DATA_DIR, "example_candlepin_data.json")
    f = open(example_data, "r")
    try:
        data = f.read()
    finally:
        f.close()
    response_body = json.loads(data)
    return 200, response_body


def mocked_rhic_serve_client_request_method(host, port, url, last_sync=None, offset=None, limit=None, debug=False, accept_gzip=False):
    example_data = os.path.join(TEST_DATA_DIR, "example_rhic_serve_data.json")
    f = open(example_data, "r")
    try:
        data = f.read()
    finally:
        f.close()
    response_body = json.loads(data)
    return 200, response_body


class BaseEntitlementTestCase(MongoTestCase):
    def setUp(self):
        super(BaseEntitlementTestCase, self).setUp()
        self.saved_candlepin_client_request_method = candlepin_client._request
        self.saved_rhic_serve_client_request_method = rhic_serve_client._request
        candlepin_client._request = mocked_candlepin_client_request_method
        rhic_serve_client._request = mocked_rhic_serve_client_request_method
        # Test Certificate Data
        # invalid cert, signed by a CA other than 'root_ca_pem'
        self.invalid_identity_cert_pem = os.path.join(TEST_DATA_DIR, "invalid_cert", "invalid.cert")
        self.invalid_identity_cert_pem = open(self.invalid_identity_cert_pem, "r").read()
        # a valid cert, signed by the below CA, 'root_ca_pem'
        self.valid_identity_cert_pem =  os.path.join(TEST_DATA_DIR, "valid_cert", "valid.cert")
        self.valid_identity_cert_pem = open(self.valid_identity_cert_pem, "r").read()
        self.deleted_identity_cert_pem = os.path.join(TEST_DATA_DIR, "deleted_cert", "deleted.cert")
        self.deleted_identity_cert_pem = open(self.deleted_identity_cert_pem, "r").read()
        # CA
        self.root_ca_pem = self.root_ca_path = config.CONFIG.get("security", "root_ca_cert")
        self.root_ca_pem = open(self.root_ca_pem, "r").read()
        # Expected data from an example session communicating with Candlepin
        self.expected_cert = "-----BEGIN CERTIFICATE-----\nMIIJ4zCCCUygAwIBAgIIIp36AfDpBMEwDQYJKoZIhvcNAQEFBQAwODEXMBUGA1UE\nAwwOaXAtMTAtNi05NC0xNDExCzAJBgNVBAYTAlVTMRAwDgYDVQQHDAdSYWxlaWdo\nMB4XDTEyMDgyODIyNDcyOFoXDTEyMDgyODIzNDcyOFowFzEVMBMGA1UEAxMMdGVz\ndHRlc3R0ZXN0MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAgJ5Cz8jQ\n+twjG6sOMM4HXuDLXlGWNNBV1N5TX/NVIUQ9Bzkgjzv1FTkpNUasASHXTjzVc7rl\nBmrXA4WN4y/y/gCHKsi4DEnjVNUq9j4aJ4NjAVLrtvh5OVIrWHZBKfcJFy06De0p\ncZWT6pUhUtW9ZqpqajRYefRUxjaiTtDNUq4rpzgLwYuAprzULd19cwpQEiY1TWlq\noVQoJy4/3q9YVvLwXquXOohdE+5iS6j/RFf7arUiJptkwyCXS7+YyPAlJDo6qnNW\nvxBLY0n2ApKGpFdgnZAq/01DIXJaNETduqdTX4w3VDgdKf4dzDq5FnnEktWHKZEk\nyKru81IiHTfH/wIDAQABo4IHkTCCB40wEQYJYIZIAYb4QgEBBAQDAgWgMAsGA1Ud\nDwQEAwIEsDBoBgNVHSMEYTBfgBSl9RwXEephltcl32HNuZwR7ZAm16E8pDowODEX\nMBUGA1UEAwwOaXAtMTAtNi05NC0xNDExCzAJBgNVBAYTAlVTMRAwDgYDVQQHDAdS\nYWxlaWdoggkA0hXeS2SIlPMwHQYDVR0OBBYEFB27SSn0Lv0Di0gXPpy1L+0/7vSg\nMBMGA1UdJQQMMAoGCCsGAQUFBwMCMCcGCysGAQQBkggJAUUBBBgMFkF3ZXNvbWUg\nT1MgU2VydmVyIEJpdHMwFAYLKwYBBAGSCAkBRQMEBQwDQUxMMBQGCysGAQQBkggJ\nAUUCBAUMAzYuMTAVBgwrBgEEAZIICQKBawEEBQwDeXVtMCMGDSsGAQQBkggJAoFr\nAQEEEgwQY29udGVudC1lbXB0eWdwZzAqBg0rBgEEAZIICQKBawECBBkMF2NvbnRl\nbnQtbGFiZWwtZW1wdHktZ3BnMB4GDSsGAQQBkggJAoFrAQUEDQwLdGVzdC12ZW5k\nb3IwHAYNKwYBBAGSCAkCgWsBBgQLDAkvZm9vL3BhdGgwEwYNKwYBBAGSCAkCgWsB\nBwQCDAAwFAYNKwYBBAGSCAkCgWsBCAQDDAExMBQGDSsGAQQBkggJAoFrAQkEAwwB\nMDAUBgsrBgEEAZIICQIBAQQFDAN5dW0wKAYMKwYBBAGSCAkCAQEBBBgMFmFsd2F5\ncy1lbmFibGVkLWNvbnRlbnQwKAYMKwYBBAGSCAkCAQECBBgMFmFsd2F5cy1lbmFi\nbGVkLWNvbnRlbnQwHQYMKwYBBAGSCAkCAQEFBA0MC3Rlc3QtdmVuZG9yMC4GDCsG\nAQQBkggJAgEBBgQeDBwvZm9vL3BhdGgvYWx3YXlzLyRyZWxlYXNldmVyMCYGDCsG\nAQQBkggJAgEBBwQWDBQvZm9vL3BhdGgvYWx3YXlzL2dwZzATBgwrBgEEAZIICQIB\nAQgEAwwBMTAVBgwrBgEEAZIICQIBAQkEBQwDMjAwMBUGDCsGAQQBkggJAoFqAQQF\nDAN5dW0wIAYNKwYBBAGSCAkCgWoBAQQPDA1jb250ZW50LW5vZ3BnMCcGDSsGAQQB\nkggJAoFqAQIEFgwUY29udGVudC1sYWJlbC1uby1ncGcwHgYNKwYBBAGSCAkCgWoB\nBQQNDAt0ZXN0LXZlbmRvcjAcBg0rBgEEAZIICQKBagEGBAsMCS9mb28vcGF0aDAT\nBg0rBgEEAZIICQKBagEHBAIMADAUBg0rBgEEAZIICQKBagEIBAMMATEwFAYNKwYB\nBAGSCAkCgWoBCQQDDAEwMBQGCysGAQQBkggJAgABBAUMA3l1bTAnBgwrBgEEAZII\nCQIAAQEEFwwVbmV2ZXItZW5hYmxlZC1jb250ZW50MCcGDCsGAQQBkggJAgABAgQX\nDBVuZXZlci1lbmFibGVkLWNvbnRlbnQwHQYMKwYBBAGSCAkCAAEFBA0MC3Rlc3Qt\ndmVuZG9yMCEGDCsGAQQBkggJAgABBgQRDA8vZm9vL3BhdGgvbmV2ZXIwJQYMKwYB\nBAGSCAkCAAEHBBUMEy9mb28vcGF0aC9uZXZlci9ncGcwEwYMKwYBBAGSCAkCAAEI\nBAMMATAwFQYMKwYBBAGSCAkCAAEJBAUMAzYwMDAUBgsrBgEEAZIICQICAQQFDAN5\ndW0wIAYMKwYBBAGSCAkCAgEBBBAMDnRhZ2dlZC1jb250ZW50MCAGDCsGAQQBkggJ\nAgIBAgQQDA50YWdnZWQtY29udGVudDAdBgwrBgEEAZIICQICAQUEDQwLdGVzdC12\nZW5kb3IwIgYMKwYBBAGSCAkCAgEGBBIMEC9mb28vcGF0aC9hbHdheXMwJgYMKwYB\nBAGSCAkCAgEHBBYMFC9mb28vcGF0aC9hbHdheXMvZ3BnMBMGDCsGAQQBkggJAgIB\nCAQDDAExMBsGDCsGAQQBkggJAgIBCgQLDAlUQUcxLFRBRzIwFQYMKwYBBAGSCAkC\niFcBBAUMA3l1bTAaBg0rBgEEAZIICQKIVwEBBAkMB2NvbnRlbnQwIAYNKwYBBAGS\nCAkCiFcBAgQPDA1jb250ZW50LWxhYmVsMB4GDSsGAQQBkggJAohXAQUEDQwLdGVz\ndC12ZW5kb3IwHAYNKwYBBAGSCAkCiFcBBgQLDAkvZm9vL3BhdGgwIQYNKwYBBAGS\nCAkCiFcBBwQQDA4vZm9vL3BhdGgvZ3BnLzAUBg0rBgEEAZIICQKIVwEIBAMMATEw\nFAYNKwYBBAGSCAkCiFcBCQQDDAEwMBwGCisGAQQBkggJBAEEDgwMUkhJQyBQcm9k\ndWN0MBQGCisGAQQBkggJBAIEBgwEMTIzNDAUBgorBgEEAZIICQQDBAYMBHJoaWMw\nEQYKKwYBBAGSCAkEBQQDDAExMCQGCisGAQQBkggJBAYEFgwUMjAxMi0wOC0yOFQy\nMjo0NzoyOFowJAYKKwYBBAGSCAkEBwQWDBQyMDEyLTA4LTI4VDIzOjQ3OjI4WjAR\nBgorBgEEAZIICQQMBAMMATAwEQYKKwYBBAGSCAkEDgQDDAEwMA0GCSqGSIb3DQEB\nBQUAA4GBAEbBBIl7zchyJ/iZ+8kc/xFXd3x0sKfnqzUTIGQYfH14Xo4tjYB0bymv\ngpXxM1+5zxwI5aiiIuvccrOgomZQIV8LHowxig+NmZb/PDCqfYw/32knReoi2bVG\nq2jpdUJLV9QdTm7KR5Lh7pPJb4foMKWEJrpztaXdMR4rfXw4Gzpe\n-----END CERTIFICATE-----\n"
        self.expected_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEAgJ5Cz8jQ+twjG6sOMM4HXuDLXlGWNNBV1N5TX/NVIUQ9Bzkg\njzv1FTkpNUasASHXTjzVc7rlBmrXA4WN4y/y/gCHKsi4DEnjVNUq9j4aJ4NjAVLr\ntvh5OVIrWHZBKfcJFy06De0pcZWT6pUhUtW9ZqpqajRYefRUxjaiTtDNUq4rpzgL\nwYuAprzULd19cwpQEiY1TWlqoVQoJy4/3q9YVvLwXquXOohdE+5iS6j/RFf7arUi\nJptkwyCXS7+YyPAlJDo6qnNWvxBLY0n2ApKGpFdgnZAq/01DIXJaNETduqdTX4w3\nVDgdKf4dzDq5FnnEktWHKZEkyKru81IiHTfH/wIDAQABAoIBAD7XlMNbVihL6Od6\n43sbH2TPJu6VpHN3m4hffJM0HFMduUfPNMZnQC83d5ftSNtgwocamBxso7xH9Xhm\nB9aKNgq/DUvtOGfgri9j3BLmcvb9biFWd481xl0odb9KQDqV1h453dSyHP6/W79R\nUC/d+SWxfD8aBmTH6afTR+iEgt2zRAQheBEsO0TKd+j3d18ijkgPx2dZyzZIRWYD\nPNEVdpFu0ECZ8PmFU14UkslZoHuD3xTy2lT2sbfJNYb7L0/72glfDvDiyz8lCl4m\ng+DRvre/a/JlxO/4ZzHAsOjrOnVJ1MYj0JpnuTVfhPYdn1vu8AUaKUaejfjBYD6Z\n9XmQ+OkCgYEAxI4HyLMGpHP6Q5XZ5NB2gvuxIyLoX7y2pLks54bsvriR6Qt0FtPA\nYV9ukYUen2+TFCAHl0XbwjKDYyX3h+FWQ07aRVVOZzsTtYA+av6c7ppnpOrFXJWS\n6oJFWL4FQuOo+Fxhqsleo/sg7tXvoxm0hHjxJRzD+mA3RGmbJFkq48UCgYEAp4RW\nnHcEGeK3+WKzt8s3G0ujTxO3qowyi9BeHA1DR0YGpHd0mdI0TAqF9u1YADBSfmj0\nXaMXw4PzctdGfBbI6kYwI6N+tzN2EdYFx1E1KfSCaEpkGFOajLr3a2lYBI7tMsJO\n3PvcWLk9RxfZwad/ADkFsbIL3SDVAJXt3dzQhPMCgYEArc8u4PI2wHvyZYuAmA8j\njWZGWNzIgchd9kHtjHtKpMiP9nVzXbA4YaLDIpmF39UJSXWdYM6cqxiCCM4NGrJP\n1stGxqLN5wldv1U9XN30JiaR2krk5Z86wHccHYJDIsgwphcDIsRZFUa/85NpCmBz\nueU80OWkA6bLmIqOb1EOVUUCgYA5gaLB/9F2mXASuqF7fNWkFyku4lPwxkQr3xIP\nizYHZ7CsER4EGDc/y3UFuaC2H+CR6LHK20wzID8Ys3JM8v1x/zpTYbMEbTQhF1nQ\nfL5Fcty5tJ/8AedSXHTHeNhwaChhfnbYQdX4106D81obssZUaz7bK4YLGVRF6TJJ\nMZ6bpQKBgQC5VyoVIrRr+w0x2ZTcJ5xPj/9L+/gS2l1o5BvzNLq6puYgz9BkMwW+\nfVpRRyaTS4BPy14qH2DqHXcqWmsfLw9Zz75wUQexkPbweFiHWB4FS2CbFHoY3w/m\ney4+0iP9HgM6TLZyuSagPkpVW/cC5i0d+STzjcsGhUeqkHIm6v4i3w==\n-----END RSA PRIVATE KEY-----\n"
        self.expected_serial = 2494424654876837057
        self.checkin = CheckIn()
        self.valid_products = ["40", "41"]
        self.valid_identity_uuid = self.checkin.extract_id_from_identity_cert(self.valid_identity_cert_pem)
        self.deleted_identity_uuid = self.checkin.extract_id_from_identity_cert(self.deleted_identity_cert_pem)
        self.expected_valid_identity_uuid = "fb647f68-aa01-4171-b62b-35c2984a5328"
        self.dummy_uuid = "11a1aa11-a11a-1a11-111a-a11111111111"

    def load_rhic_data(self):
        item = {}
        item["uuid"] = self.valid_identity_uuid
        item["engineering_ids"] = self.valid_products
        create_or_update_consumer_identity(item)
        item = {}
        item["uuid"] = self.deleted_identity_uuid
        item["engineering_ids"] = self.valid_products
        item["deleted"] = True
        create_or_update_consumer_identity(item)

    def tearDown(self):
        super(BaseEntitlementTestCase, self).tearDown()
        key = SyncRHICServeThread.__name__
        # Before quitting tests, wait for any spawned threads to complete and cleanup
        for count in range(0,100):
            if not identity.JOBS.has_key(key):
                break
            print "Waiting for %s to finish, is_alive() = %s" % (key, identity.JOBS[key].is_alive())
            time.sleep(.01)
        candlepin_client._request = self.saved_candlepin_client_request_method
        rhic_serve_client._request = self.saved_rhic_serve_client_request_method
        # NOTE:  There is a potential timing issue which requires us to drop the database
        #        after all identity.JOBS have completed.  Failure to do this can leave the database
        #        in a bad state
        self.drop_database_and_reconnect()

