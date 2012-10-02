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

from splice.common import candlepin_client
from splice.common import config
from splice.common import rhic_serve_client
from splice.common import utils
from splice.common.certs import CertUtils
from splice.common.exceptions import UnsupportedDateFormatException, UnexpectedStatusCodeException, NotFoundConsumerIdentity
from splice.common.identity import create_or_update_consumer_identity, sync_from_rhic_serve, \
        sync_from_rhic_serve_blocking, SyncRHICServeThread
from splice.entitlement.checkin import CheckIn
from splice.entitlement.models import ConsumerIdentity, IdentitySyncInfo, RHICLookupTask, ProductUsage
from splice.managers import identity_lookup

from splice.common import identity

TEST_DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "test_data")
LOG = getLogger(__name__)

#TODO Break these tests out to separate files and allow to run from nosetests outside of 'python manage.py test entitlement'

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


class MongoTestsTestCase(MongoTestCase):

    def test_mongo_cleanup_is_working(self):
        class MongoTestEntry(Document):
            uuid = StringField(required=True, unique=True)
        m = MongoTestEntry(uuid="new_entry")
        m.save()
        lookup = MongoTestEntry.objects()
        self.assertEqual(len(lookup), 1)
        self.drop_database_and_reconnect()
        lookup = MongoTestEntry.objects()
        self.assertEqual(len(lookup), 0)

    def test_save_duplicates(self):
        class Simple(Document):
            name = StringField(required=True, unique=True)
        @classmethod
        def pre_save(cls, sender, document, **kwargs):
            document.name = "Hi %s" % (document.name)
        def __str__(self):
            return "Simple: name = %s" % (self.name)

        fred = Simple(name="Fred")
        fred.save()
        duplicate = Simple(name=fred.name)
        caught = False
        try:
            duplicate.save()
        except:
            caught = True
        self.assertTrue(caught)

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

def mocked_rhic_serve_client_request_method(host, port, url, last_sync=None, debug=False):
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


class CandlepinClientTest(BaseEntitlementTestCase):

    def setUp(self):
        super(CandlepinClientTest, self).setUp()

    def tearDown(self):
        super(CandlepinClientTest, self).tearDown()

    def test_get_entitlement(self):
        cert_info = candlepin_client.get_entitlement(host="localhost", port=0, url="mocked",
            requested_products=[4], identity="dummy identity", username="", password="")
        self.assertEquals(len(cert_info), 1)
        self.assertEquals(cert_info[0][0], self.expected_cert)
        self.assertEquals(cert_info[0][1], self.expected_key)


class CertUtilsTest(BaseEntitlementTestCase):
    """
    Tests to exercise splice.common.certs.CertUtils
    """
    def setUp(self):
        super(CertUtilsTest, self).setUp()
        self.cert_utils = CertUtils()

    def tearDown(self):
        super(CertUtilsTest, self).tearDown()

    def test_validate_certificate_pem_valid(self):
        self.assertTrue(self.cert_utils.validate_certificate_pem(
            self.valid_identity_cert_pem, self.root_ca_pem))

    def test_validate_certificate_pem_invalid(self):
        self.assertFalse(self.cert_utils.validate_certificate_pem(
            self.invalid_identity_cert_pem, self.root_ca_pem))

    def test_get_subject_pieces(self):
        pieces = self.cert_utils.get_subject_pieces(self.valid_identity_cert_pem)
        self.assertEquals(len(pieces), 1)
        self.assertEquals(pieces["CN"], self.expected_valid_identity_uuid)

class EntitlementResourceTest(BaseEntitlementTestCase):

    def setUp(self):
        super(EntitlementResourceTest, self).setUp()
        self.username = "admin"
        self.password = "admin"
        # TODO add auth
        # self.user = User.objects.create_user(self.username, 'admin@example.com', self.password)
        self.post_data = {
            'consumer_identifier': "52:54:00:15:E7:69",
            'products': self.valid_products,
            'system_facts': {"tbd":"values"}
        }
        self.load_rhic_data()

    def tearDown(self):
        super(EntitlementResourceTest, self).tearDown()

    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

    def test_post_entitlement_valid_identity(self):
        LOG.info("Entered 'test_post_entitlement_valid_identity'")
        resp = self.api_client.post('/api/v1/entitlement/BOGUS_IDENTITY/', format='json',
            authentication=self.get_credentials(), data=self.post_data,
            SSL_CLIENT_CERT=self.valid_identity_cert_pem)
        LOG.info("Completed call to entitlement checkin from unit test: test_post_entitlement_valid_identity")
        if resp.status_code != 200:
            print resp.status_code, resp
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(resp['Content-Type'].startswith('application/json'))
        self.assertValidJSON(resp.content)

        deserialized = self.deserialize(resp)
        self.assertEquals(len(deserialized["certs"]), 1)
        self.assertEquals(deserialized["certs"][0][0], self.expected_cert)
        self.assertEquals(deserialized["certs"][0][1], self.expected_key)
        self.assertEquals(deserialized["certs"][0][2], self.expected_serial)

    def test_post_entitlement_invalid_identity(self):
        resp = self.api_client.post('/api/v1/entitlement/BOGUS_IDENTITY/',
            format='json',
            authentication=self.get_credentials(),
            data=self.post_data,
            SSL_CLIENT_CERT=self.invalid_identity_cert_pem)
        self.assertHttpForbidden(resp)
        self.assertEqual("Unable to verify consumer's identity certificate was signed by configured CA", resp.content)

    def test_post_entitlement_deleted_identity(self):
        resp = self.api_client.post('/api/v1/entitlement/%s/' % (self.deleted_identity_uuid),
            format='json',
            authentication=self.get_credentials(),
            data=self.post_data,
            SSL_CLIENT_CERT=self.deleted_identity_cert_pem)
        self.assertHttpGone(resp)
        self.assertEqual("Exception: consumer identity '%s' has been deleted." % (self.deleted_identity_uuid), resp.content)

class IdentityLookupTest(BaseEntitlementTestCase):
    def setUp(self):
        super(IdentityLookupTest, self).setUp()

    def tearDown(self):
        super(IdentityLookupTest, self).tearDown()

    def test_update_rhic_lookup_task(self):
        task_a = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False, task_id=None)
        task_a.save()
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(task_a.uuid, found[0].uuid)
        self.assertIsNone(found[0].task_id)
        prior_modified = task_a.modified

        # Ensure that 'modified' has been updated to new time
        # and the 'task_id' has been noted
        task_id = "1"
        ret_val = identity_lookup.update_rhic_lookup_task(task_a.uuid, task_id)
        self.assertEquals(ret_val.uuid, task_a.uuid)
        self.assertFalse(ret_val.completed)
        self.assertEquals(ret_val.task_id, task_id)
        self.assertTrue(ret_val.modified > prior_modified)

        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task_a.uuid)
        self.assertFalse(found[0].completed)
        self.assertEquals(found[0].task_id, task_id)
        # TODO Look into why we need to localize isodates that come back from mongo,
        # looks like it's dropping off the timezone offset
        self.assertTrue(pytz.UTC.localize(found[0].modified) > prior_modified)


    def test_complete_rhic_lookup_task_200(self):
        task = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False, task_id=None)
        task.save()
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)

        # Mark as '200', a successful complete which will remove the task from the lookup db
        accepted = 200
        ret_val = identity_lookup.complete_rhic_lookup_task(task.uuid, accepted)
        self.assertIsNone(ret_val)
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 0)

    def test_complete_rhic_lookup_task_404(self):
        task = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False, task_id=None)
        task.save()
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)

        # Mark as '404', task finished and received answer RHIC is unknown
        # task should be cached in DB with '404' status_code
        # it should be marked as 'completed=True'
        not_found = 404
        ret_val = identity_lookup.complete_rhic_lookup_task(task.uuid, not_found)
        self.assertIsNotNone(ret_val)
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)
        self.assertIsNone(found[0].task_id)
        self.assertEquals(found[0].status_code, not_found)
        self.assertTrue(found[0].completed)

    def test_complete_rhic_lookup_task_202(self):
        task = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False, task_id=None)
        task.save()
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)

        # Mark as '202', meaning we haven't found an answer yet, let the tasks continue
        # task should remain in DB, should be marked as 'completed=False'
        in_progress = 202
        ret_val = identity_lookup.complete_rhic_lookup_task(task.uuid, in_progress)
        self.assertIsNotNone(ret_val)
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)
        self.assertIsNone(found[0].task_id)
        self.assertEquals(found[0].status_code, in_progress)
        self.assertFalse(found[0].completed)


    def test_complete_rhic_lookup_task_unexpected_value(self):
        task = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False, task_id=None)
        task.save()
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)

        # Mark task with an odd unexpected value, we will mark the task as completed=True
        # and store the status_code
        unexpected = 123
        ret_val = identity_lookup.complete_rhic_lookup_task(task.uuid, unexpected)
        self.assertIsNotNone(ret_val)
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 1)
        self.assertEquals(found[0].uuid, task.uuid)
        self.assertIsNone(found[0].task_id)
        self.assertEquals(found[0].status_code, unexpected)
        self.assertTrue(found[0].completed)


class IdentityTest(BaseEntitlementTestCase):
    def setUp(self):
        super(IdentityTest, self).setUp()

    def tearDown(self):
        super(IdentityTest, self).tearDown()

    def test_get_all_rhics(self):
        rhics = rhic_serve_client.get_all_rhics(host="localhost", port=0, url="mocked")
        self.assertEquals(len(rhics), 3)

    def test_sync_from_rhic_serve_blocking(self):
        self.assertEqual(len(identity.JOBS), 0)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 0)
        sync_from_rhic_serve_blocking()
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 3)
        expected_rhics = ["fb647f68-aa01-4171-b62b-35c2984a5328",
                          "ef8548a9-c874-42a8-b5dc-bc5ab0b34cd7",
                          "a17013d8-e896-4749-9b37-8606d62bf643"]
        for r in rhics:
            self.assertIn(str(r.uuid), expected_rhics)

    def test_sync_from_rhic_serve_threaded(self):
        self.assertEqual(len(identity.JOBS), 0)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 0)
        sync_thread = sync_from_rhic_serve()
        for index in range(0,120):
            if not sync_thread.finished:
                time.sleep(.05)
        self.assertTrue(sync_thread.finished)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 3)
        expected_rhics = ["fb647f68-aa01-4171-b62b-35c2984a5328",
                          "ef8548a9-c874-42a8-b5dc-bc5ab0b34cd7",
                          "a17013d8-e896-4749-9b37-8606d62bf643"]
        for r in rhics:
            self.assertIn(str(r.uuid), expected_rhics)

    def test_sync_that_removes_old_rhics(self):
        self.assertEqual(len(identity.JOBS), 0)
        # Create one dummy RHIC which our sync should remove
        item = {}
        item["uuid"] = "180ed55f-c3fb-4249-ac4c-52e440cd9301"
        item["engineering_ids"] = ["1","2"]
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        sync_from_rhic_serve_blocking()
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 3)
        expected_rhics = ["fb647f68-aa01-4171-b62b-35c2984a5328",
                          "ef8548a9-c874-42a8-b5dc-bc5ab0b34cd7",
                          "a17013d8-e896-4749-9b37-8606d62bf643"]
        for r in rhics:
            self.assertIn(str(r.uuid), expected_rhics)

    def test_sync_where_existing_rhics_product_mapping_changes(self):
        self.assertEqual(len(identity.JOBS), 0)
        # Create a RHIC with products that will change after sync
        item = {}
        item["uuid"] = "fb647f68-aa01-4171-b62b-35c2984a5328"
        item["engineering_ids"] = ["1", "2"]
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        sync_from_rhic_serve_blocking()
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 3)
        expected_rhics = ["fb647f68-aa01-4171-b62b-35c2984a5328",
                          "ef8548a9-c874-42a8-b5dc-bc5ab0b34cd7",
                          "a17013d8-e896-4749-9b37-8606d62bf643"]
        for r in rhics:
            self.assertIn(str(r.uuid), expected_rhics)
        # Ensure that the products have been updated
        rhic_under_test = ConsumerIdentity.objects(uuid=item["uuid"]).first()
        self.assertTrue(rhic_under_test)
        expected_products = ["183", "83", "69"]
        for ep in expected_products:
            self.assertTrue(ep in rhic_under_test.engineering_ids)

    def test_get_current_rhic_lookup_tasks(self):
        cfg = config.get_rhic_serve_config_info()
        # Create a valid, in_progress task
        task_a = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False)
        task_a.save()
        # Create a completed task
        task_b = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a22222222222", completed=True,
            initiated=datetime.now(tzutc()),
            modified=datetime.now(tzutc()))
        task_b.save()
        # Create a timedout incomplete task
        timeout_in_minutes = cfg["single_rhic_lookup_timeout_in_minutes"]
        expired_time = datetime.now(tzutc()) - timedelta(minutes=timeout_in_minutes+1)
        task_c = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a333333333333", completed=False, initiated=expired_time)
        task_c.save()
        # Create a completed expired task
        expired_hours = cfg["single_rhic_lookup_cache_unknown_in_hours"]
        expired_time = datetime.now(tzutc()) - timedelta(hours=expired_hours+1)
        task_d = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a444444444444", completed=True, modified=expired_time)
        task_d.save()

        # Ensure all tasks where created and have been saved in mongo
        current_tasks = [x.uuid for x in RHICLookupTask.objects()]
        for t in [task_a, task_b, task_c, task_d]:
            self.assertTrue(t.uuid in current_tasks)

        # In-progress, valid task
        task = identity.get_current_rhic_lookup_tasks(task_a.uuid)
        self.assertIsNotNone(task)
        self.assertEquals(task.uuid, task_a.uuid)

        # Completed, valid task
        task = identity.get_current_rhic_lookup_tasks(task_b.uuid)
        self.assertIsNotNone(task)
        self.assertEquals(task.uuid, task_b.uuid)

        # In-progress, timed out task
        task = identity.get_current_rhic_lookup_tasks(task_c.uuid)
        self.assertIsNone(task)
        found = [x.uuid for x in RHICLookupTask.objects()]
        self.assertTrue(task_c.uuid not in found)

        # Completed, cache time expired task
        task = identity.get_current_rhic_lookup_tasks(task_d.uuid)
        self.assertIsNone(task)
        found = [x.uuid for x in RHICLookupTask.objects()]
        self.assertTrue(task_d.uuid not in found)

        # Be sure of the 4 tasks we created, the expired and timedout were removed
        # while the 2 good tasks remained
        self.assertEquals(len(found), 2)
        self.assertTrue(task_a.uuid in found)
        self.assertTrue(task_b.uuid in found)

    def test_is_rhic_lookup_task_expired(self):
        # Create a valid, in_progress task
        task_a = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False)
        task_a.save()
        self.assertFalse(identity.is_rhic_lookup_task_expired(task_a))

        # Create a completed task
        task_b = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a22222222222", completed=True,
            initiated=datetime.now(tzutc()),
            modified=datetime.now(tzutc()))
        task_b.save()
        self.assertFalse(identity.is_rhic_lookup_task_expired(task_b))

        # Create a timedout incomplete task
        cfg = config.get_rhic_serve_config_info()
        timeout_in_minutes = cfg["single_rhic_lookup_timeout_in_minutes"]
        expired_time = datetime.now(tzutc()) - timedelta(minutes=timeout_in_minutes+1)
        task_c = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a333333333333", completed=False, initiated=expired_time)
        task_c.save()
        self.assertTrue(identity.is_rhic_lookup_task_expired(task_c))

        # Create a completed expired task
        expired_hours = cfg["single_rhic_lookup_cache_unknown_in_hours"]
        expired_time = datetime.now(tzutc()) - timedelta(hours=expired_hours+1)
        task_d = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a444444444444", completed=True, modified=expired_time)
        task_d.save()
        self.assertTrue(identity.is_rhic_lookup_task_expired(task_d))


    def test_purge_expired_rhic_lookups(self):
        cfg = config.get_rhic_serve_config_info()
        # Create a valid, in_progress task
        task_a = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False)
        task_a.save()
        # Create a completed task
        task_b = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a22222222222", completed=True,
            initiated=datetime.now(tzutc()),
            modified=datetime.now(tzutc()))
        task_b.save()
        # Create a timedout incomplete task
        timeout_in_minutes = cfg["single_rhic_lookup_timeout_in_minutes"]
        expired_time = datetime.now(tzutc()) - timedelta(minutes=timeout_in_minutes+1)
        task_c = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a333333333333", completed=False, initiated=expired_time)
        task_c.save()
        # Create a completed expired task
        expired_hours = cfg["single_rhic_lookup_cache_unknown_in_hours"]
        expired_time = datetime.now(tzutc()) - timedelta(hours=expired_hours+1)
        task_d = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a444444444444", completed=True, modified=expired_time)
        task_d.save()

        identity.purge_expired_rhic_lookups()
        found = RHICLookupTask.objects()
        self.assertEquals(len(found), 2)
        for f in found:
            self.assertTrue(f.uuid in [task_a.uuid, task_b.uuid])
            self.assertTrue(f.uuid not in [task_c.uuid, task_d.uuid])

    def test_get_in_progress_rhic_lookups(self):
        # Create a valid, in_progress task
        task_a = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a11111111111", completed=False)
        task_a.save()
        # Create a completed task
        task_b = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a22222222222", completed=True,
            initiated=datetime.now(tzutc()),
            modified=datetime.now(tzutc()))
        task_b.save()
        # Create a timedout incomplete task
        cfg = config.get_rhic_serve_config_info()
        timeout_in_minutes = cfg["single_rhic_lookup_timeout_in_minutes"]
        expired_time = datetime.now(tzutc()) - timedelta(minutes=timeout_in_minutes+1)
        task_c = RHICLookupTask(uuid="11a1aa11-a11a-1a11-111a-a333333333333", completed=False, initiated=expired_time)
        task_c.save()
        current_tasks = identity.get_in_progress_rhic_lookups()
        self.assertEquals(len(current_tasks), 1)
        self.assertEquals(current_tasks[0].uuid, task_a.uuid)

    def test_delete_rhic_lookup(self):
        self.assertFalse(identity.delete_rhic_lookup(None))

        task = RHICLookupTask(uuid=self.dummy_uuid)
        task.save()
        self.assertTrue(identity.delete_rhic_lookup(task))
        self.assertEquals(len(RHICLookupTask.objects()), 0)

    def test_simulate_multiple_sync_threads_at_sametime(self):
        # Simulate a syncthread was created and hasn't finished yet
        key = SyncRHICServeThread.__name__
        # Skipping lock on identity.JOBS
        dummy_job = SyncRHICServeThread()
        identity.JOBS[key] = dummy_job
        # This thread is not in a finished state, therefore next job we try to create should return None
        # and do nothing, letting this job finish
        sync_thread = sync_from_rhic_serve()
        self.assertIsNone(sync_thread)
        # Now we simulate the job finishing and cleaning up it's reference
        dummy_job.remove_reference()
        # Ensure JOBS has been cleanedup
        self.assertEqual(len(identity.JOBS), 0)

    def test_create_new_consumer_identity(self):
        item = {}
        item["uuid"] = "734ed55f-c3fb-4249-ac4c-52e440cd9304"
        item["engineering_ids"] = ["1", "2"]
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        self.assertEquals(str(rhics[0].uuid), item["uuid"])
        self.assertEquals(rhics[0].engineering_ids, item["engineering_ids"])

    def test_update_consumer_identity(self):
        item = {}
        item["uuid"] = "734ed55f-c3fb-4249-ac4c-52e440cd9304"
        item["engineering_ids"] = ["1", "2"]
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        self.assertEquals(str(rhics[0].uuid), item["uuid"])
        self.assertEquals(rhics[0].engineering_ids, item["engineering_ids"])
        self.assertEquals(len(rhics[0].engineering_ids), 2)
        # Add a product to engineering ids and update
        item["engineering_ids"] += "3"
        self.assertNotEquals(rhics[0].engineering_ids, item["engineering_ids"])
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        self.assertEquals(str(rhics[0].uuid), item["uuid"])
        self.assertEquals(rhics[0].engineering_ids, item["engineering_ids"])
        self.assertEquals(len(rhics[0].engineering_ids), 3)


    def test_update_consumer_that_has_been_marked_as_deleted(self):
        item = {}
        item["uuid"] = "734ed55f-c3fb-4249-ac4c-52e440cd9304"
        item["engineering_ids"] = ["1", "2"]
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        self.assertEquals(str(rhics[0].uuid), item["uuid"])
        self.assertEquals(rhics[0].engineering_ids, item["engineering_ids"])
        item["deleted"] = True
        create_or_update_consumer_identity(item)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        self.assertEquals(str(rhics[0].uuid), item["uuid"])
        self.assertTrue(rhics[0].deleted)

    def test_get_last_sync_timestamp(self):
        server_hostname = "a.b.c.example.com"
        sync_info = IdentitySyncInfo(server_hostname=server_hostname)
        sync_info.last_sync = datetime.now(tzutc())
        sync_info.save()

        found = identity.get_last_sync_timestamp(server_hostname)
        self.assertIsNotNone(found)
        created = sync_info.last_sync
        self.assertEquals(created.year, found.year)
        self.assertEquals(created.month, found.month)
        self.assertEquals(created.day, found.day)
        self.assertEquals(created.hour, found.hour)
        self.assertEquals(created.minute, found.minute)
        self.assertEquals(created.second, found.second)

    def test_save_duplicate(self):
        server_hostname = "simple.example.com"
        sync_info = IdentitySyncInfo(server_hostname=server_hostname)
        sync_info.last_sync = datetime.now(tzutc())
        sync_info.save()
        self.assertEquals(len(IdentitySyncInfo.objects()), 1 )

        dup = IdentitySyncInfo(server_hostname=server_hostname)
        dup.last_sync = datetime.now(tzutc())
        caught = False
        try:
            dup.save()
        except:
            caught = True
        data =  IdentitySyncInfo.objects()
        self.assertEquals(len(data), 1)
        self.assertTrue(caught)

    def test_save_last_sync(self):
        server_hostname = "a.b.c.example.com"
        sync_info = IdentitySyncInfo(server_hostname=server_hostname)
        sync_info.last_sync = datetime.now(tzutc())
        sync_info.save()
        key = utils.sanitize_key_for_mongo(server_hostname)
        lookup = IdentitySyncInfo.objects(server_hostname=key)
        self.assertIsNotNone(lookup)
        self.assertEquals(len(lookup), 1)
        created = sync_info.last_sync
        found = lookup[0].last_sync
        self.assertEquals(created.year, found.year)
        self.assertEquals(created.month, found.month)
        self.assertEquals(created.day, found.day)
        self.assertEquals(created.hour, found.hour)
        self.assertEquals(created.minute, found.minute)
        self.assertEquals(created.second, found.second)

    # TODO:  Update sample rhic data for more info


class CheckInTest(BaseEntitlementTestCase):
    """
    Tests to exercise splice.entitlement.checkin.CheckIn
    """
    def setUp(self):
        super(CheckInTest, self).setUp()
        self.load_rhic_data()

    def tearDown(self):
        super(CheckInTest, self).tearDown()

    def test_validate_cert_valid(self):
        self.assertTrue(self.checkin.validate_cert(self.valid_identity_cert_pem))

    def test_validate_cert_invalid(self):
        self.assertFalse(self.checkin.validate_cert(self.invalid_identity_cert_pem))

    def test_extract_id_from_identity_cert(self):
        # below is example of subject from test data
        # $ openssl x509 -subject -in test_data/valid_cert/sample_rhic_valid.pem
        #        subject=/CN=dbcbc8e1-5b37-4a77-9db1-faf4ef29307d
        self.assertEquals(
            self.checkin.extract_id_from_identity_cert(self.valid_identity_cert_pem),
            self.expected_valid_identity_uuid)

    def test_check_access_allowed(self):
        identity = ConsumerIdentity.objects(uuid=self.valid_identity_uuid).first()
        allowed_products, unallowed_products = self.checkin.check_access(identity, self.valid_products)
        for p in self.valid_products:
            self.assertTrue(p in allowed_products)
        self.assertEquals(len(unallowed_products), 0)

    def test_check_access_unallowed(self):
        identity = ConsumerIdentity.objects(uuid=self.valid_identity_uuid).first()
        allowed_products, unallowed_products = self.checkin.check_access(identity, ["100", "101"])
        self.assertTrue("100" in unallowed_products)
        self.assertTrue("101" in unallowed_products)
        self.assertEquals(len(allowed_products), 0)

        allowed_products, unallowed_products = self.checkin.check_access(identity, [self.valid_products[0], "101"])
        self.assertTrue(self.valid_products[0] in allowed_products)
        self.assertTrue("101" in unallowed_products)
        self.assertEquals(len(allowed_products), 1)
        self.assertEquals(len(unallowed_products), 1)

    def test_not_found(self):
    # Create a stored rhic lookup that is valid and set response to 404
        rhic_uuid = "11a1aa11-a11a-1a11-111a-a22222222222"
        task = RHICLookupTask(uuid=rhic_uuid, completed=True,
            initiated=datetime.now(tzutc()),
            modified=datetime.now(tzutc()),
            status_code=404)
        task.save()
        # Verify we return this '404'
        caught = False
        try:
            self.checkin.get_identity_object(rhic_uuid)
        except NotFoundConsumerIdentity, e:
            caught = True
        self.assertTrue(caught)

    def test_unexpected_cached_status_code(self):
        # Create a stored rhic lookup that is valid and set response to 483
        # Verify we return this 'unexpected status code'
        rhic_uuid = "11a1aa11-a11a-1a11-111a-a22222222222"
        task = RHICLookupTask(uuid=rhic_uuid, completed=True,
            initiated=datetime.now(tzutc()),
            modified=datetime.now(tzutc()),
            status_code=483)
        task.save()
        caught = False
        try:
            self.checkin.get_identity_object(rhic_uuid)
        except UnexpectedStatusCodeException, e:
            caught = True
            self.assertEqual(e.status_code, 483)
        self.assertTrue(caught)

class UtilsTest(BaseEntitlementTestCase):
    """
    Tests to exercise splice.common.utils
    """
    def setUp(self):
        super(UtilsTest, self).setUp()

    def tearDown(self):
        super(UtilsTest, self).tearDown()

    def test_sanitize_dict_for_mongo(self):
        bad_dot_key = "bad.value.with.dots"
        fixed_bad_dot_key = "bad_dot_value_dot_with_dot_dots"
        bad_dollar_key = "dolla$dolla$"
        fixed_bad_dollar_key = "dolla_dollarsign_dolla_dollarsign_"
        a = {bad_dot_key: "1",
             bad_dollar_key: "2"}
        sanitized = utils.sanitize_dict_for_mongo(a)
        self.assertEquals(len(sanitized), 2)
        self.assertTrue(sanitized.has_key(fixed_bad_dot_key))
        self.assertTrue(sanitized.has_key(fixed_bad_dollar_key))
        self.assertEquals(sanitized[fixed_bad_dot_key], a[bad_dot_key])
        self.assertEquals(sanitized[fixed_bad_dollar_key], a[bad_dollar_key])

        expected_same = utils.sanitize_dict_for_mongo(sanitized)
        self.assertEquals(expected_same, sanitized)


    def test_sanitize_key_for_mongo(self):
        bad_dots_in_list_key = ["bad.value.1", [["bad.value.2"]]]
        fixed_bad_key = ["bad_dot_value_dot_1", [["bad_dot_value_dot_2"]]]
        sanitized = utils.sanitize_key_for_mongo(bad_dots_in_list_key)
        self.assertEquals(len(sanitized), len(fixed_bad_key))
        for key in sanitized:
            self.assertIn(key, fixed_bad_key)
        expected_same = utils.sanitize_key_for_mongo(sanitized)
        self.assertEquals(expected_same, sanitized)


    def test_convert_to_datetime(self):
        # Ensure we can handle None being passed in
        self.assertIsNone(utils.convert_to_datetime(None))

        a = '2012-09-19T19:01:55.008000+00:00'
        dt_a = utils.convert_to_datetime(a)
        self.assertEquals(dt_a.year, 2012)
        self.assertEquals(dt_a.month, 9)
        self.assertEquals(dt_a.day, 19)
        self.assertEquals(dt_a.hour, 19)
        self.assertEquals(dt_a.minute, 1)
        self.assertEquals(dt_a.microsecond, 8000)
        self.assertEquals(dt_a.second, 55)

        b = '2012-09-19T19:01:55+00:00'
        dt_b = utils.convert_to_datetime(b)
        self.assertEquals(dt_a.year, 2012)
        self.assertEquals(dt_a.month, 9)
        self.assertEquals(dt_a.day, 19)
        self.assertEquals(dt_a.hour, 19)
        self.assertEquals(dt_a.minute, 1)
        self.assertEquals(dt_a.second, 55)

        c = '2012-09-19T19:01:55'
        dt_c = utils.convert_to_datetime(c)
        self.assertEquals(dt_c.year, 2012)
        self.assertEquals(dt_c.month, 9)
        self.assertEquals(dt_c.day, 19)
        self.assertEquals(dt_c.hour, 19)
        self.assertEquals(dt_c.minute, 1)
        self.assertEquals(dt_c.second, 55)

        caught  = False
        bad_value = 'BadValue'
        try:
            utils.convert_to_datetime(bad_value)
            self.assertTrue(False) # Exception should be raised
        except UnsupportedDateFormatException, e:
            caught = True
            self.assertEquals(e.date_str, bad_value)
        self.assertTrue(caught)
