import json
import os
import time


from tastypie.test import ResourceTestCase

from mongoengine.connection import connect, disconnect
from django.conf import settings

from splice.common import candlepin_client
from splice.common import rhic_serve_client
from splice.common import utils
from splice.common.certs import CertUtils
from splice.common.identity import create_new_consumer_identity, sync_from_rhic_serve, sync_from_rhic_serve_blocking
from splice.entitlement.checkin import CheckIn, CertValidationException
from splice.entitlement.models import ConsumerIdentity

TEST_DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "test_data")

#TODO Break these tests out to separate files and allow to run from nosetests outside of 'python manage.py test entitlement'

# Adapted From:
# https://github.com/vandersonmota/mongoengine_django_tests/blob/master/mongotest.py
class MongoTestCase(ResourceTestCase):
    """
    TestCase class that clear the collection between the tests
    """
    db_name = 'test_%s' % settings.MONGO_DATABASE_NAME
    def __init__(self, methodName='runtest'):
        super(MongoTestCase, self).__init__(methodName)
        disconnect()
        self.db = connect(self.db_name)

    def _post_teardown(self):
        super(MongoTestCase, self)._post_teardown()
        self.db.drop_database(self.db_name)

    def drop_database_and_reconnect(self):
        disconnect()
        self.db.drop_database(self.db_name)
        self.db = connect(self.db_name)

def mocked_candlepin_client_request_method(host, port, url, installed_product,
                          identity, username, password, debug=False):
    example_data = os.path.join(TEST_DATA_DIR, "example_candlepin_data.json")
    f = open(example_data, "r")
    try:
        data = f.read()
    finally:
        f.close()
    response_body = json.loads(data)
    return 200, response_body

def mocked_rhic_serve_client_request_method(host, port, url, debug=False):
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
        # CA
        self.root_ca_pem = os.path.join(TEST_DATA_DIR, "valid_cert", "ca.cert")
        self.root_ca_pem = open(self.root_ca_pem, "r").read()
        # Expected data from an example session communicating with Candlepin
        self.expected_cert = "-----BEGIN CERTIFICATE-----\nMIIJ4zCCCUygAwIBAgIIIp36AfDpBMEwDQYJKoZIhvcNAQEFBQAwODEXMBUGA1UE\nAwwOaXAtMTAtNi05NC0xNDExCzAJBgNVBAYTAlVTMRAwDgYDVQQHDAdSYWxlaWdo\nMB4XDTEyMDgyODIyNDcyOFoXDTEyMDgyODIzNDcyOFowFzEVMBMGA1UEAxMMdGVz\ndHRlc3R0ZXN0MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAgJ5Cz8jQ\n+twjG6sOMM4HXuDLXlGWNNBV1N5TX/NVIUQ9Bzkgjzv1FTkpNUasASHXTjzVc7rl\nBmrXA4WN4y/y/gCHKsi4DEnjVNUq9j4aJ4NjAVLrtvh5OVIrWHZBKfcJFy06De0p\ncZWT6pUhUtW9ZqpqajRYefRUxjaiTtDNUq4rpzgLwYuAprzULd19cwpQEiY1TWlq\noVQoJy4/3q9YVvLwXquXOohdE+5iS6j/RFf7arUiJptkwyCXS7+YyPAlJDo6qnNW\nvxBLY0n2ApKGpFdgnZAq/01DIXJaNETduqdTX4w3VDgdKf4dzDq5FnnEktWHKZEk\nyKru81IiHTfH/wIDAQABo4IHkTCCB40wEQYJYIZIAYb4QgEBBAQDAgWgMAsGA1Ud\nDwQEAwIEsDBoBgNVHSMEYTBfgBSl9RwXEephltcl32HNuZwR7ZAm16E8pDowODEX\nMBUGA1UEAwwOaXAtMTAtNi05NC0xNDExCzAJBgNVBAYTAlVTMRAwDgYDVQQHDAdS\nYWxlaWdoggkA0hXeS2SIlPMwHQYDVR0OBBYEFB27SSn0Lv0Di0gXPpy1L+0/7vSg\nMBMGA1UdJQQMMAoGCCsGAQUFBwMCMCcGCysGAQQBkggJAUUBBBgMFkF3ZXNvbWUg\nT1MgU2VydmVyIEJpdHMwFAYLKwYBBAGSCAkBRQMEBQwDQUxMMBQGCysGAQQBkggJ\nAUUCBAUMAzYuMTAVBgwrBgEEAZIICQKBawEEBQwDeXVtMCMGDSsGAQQBkggJAoFr\nAQEEEgwQY29udGVudC1lbXB0eWdwZzAqBg0rBgEEAZIICQKBawECBBkMF2NvbnRl\nbnQtbGFiZWwtZW1wdHktZ3BnMB4GDSsGAQQBkggJAoFrAQUEDQwLdGVzdC12ZW5k\nb3IwHAYNKwYBBAGSCAkCgWsBBgQLDAkvZm9vL3BhdGgwEwYNKwYBBAGSCAkCgWsB\nBwQCDAAwFAYNKwYBBAGSCAkCgWsBCAQDDAExMBQGDSsGAQQBkggJAoFrAQkEAwwB\nMDAUBgsrBgEEAZIICQIBAQQFDAN5dW0wKAYMKwYBBAGSCAkCAQEBBBgMFmFsd2F5\ncy1lbmFibGVkLWNvbnRlbnQwKAYMKwYBBAGSCAkCAQECBBgMFmFsd2F5cy1lbmFi\nbGVkLWNvbnRlbnQwHQYMKwYBBAGSCAkCAQEFBA0MC3Rlc3QtdmVuZG9yMC4GDCsG\nAQQBkggJAgEBBgQeDBwvZm9vL3BhdGgvYWx3YXlzLyRyZWxlYXNldmVyMCYGDCsG\nAQQBkggJAgEBBwQWDBQvZm9vL3BhdGgvYWx3YXlzL2dwZzATBgwrBgEEAZIICQIB\nAQgEAwwBMTAVBgwrBgEEAZIICQIBAQkEBQwDMjAwMBUGDCsGAQQBkggJAoFqAQQF\nDAN5dW0wIAYNKwYBBAGSCAkCgWoBAQQPDA1jb250ZW50LW5vZ3BnMCcGDSsGAQQB\nkggJAoFqAQIEFgwUY29udGVudC1sYWJlbC1uby1ncGcwHgYNKwYBBAGSCAkCgWoB\nBQQNDAt0ZXN0LXZlbmRvcjAcBg0rBgEEAZIICQKBagEGBAsMCS9mb28vcGF0aDAT\nBg0rBgEEAZIICQKBagEHBAIMADAUBg0rBgEEAZIICQKBagEIBAMMATEwFAYNKwYB\nBAGSCAkCgWoBCQQDDAEwMBQGCysGAQQBkggJAgABBAUMA3l1bTAnBgwrBgEEAZII\nCQIAAQEEFwwVbmV2ZXItZW5hYmxlZC1jb250ZW50MCcGDCsGAQQBkggJAgABAgQX\nDBVuZXZlci1lbmFibGVkLWNvbnRlbnQwHQYMKwYBBAGSCAkCAAEFBA0MC3Rlc3Qt\ndmVuZG9yMCEGDCsGAQQBkggJAgABBgQRDA8vZm9vL3BhdGgvbmV2ZXIwJQYMKwYB\nBAGSCAkCAAEHBBUMEy9mb28vcGF0aC9uZXZlci9ncGcwEwYMKwYBBAGSCAkCAAEI\nBAMMATAwFQYMKwYBBAGSCAkCAAEJBAUMAzYwMDAUBgsrBgEEAZIICQICAQQFDAN5\ndW0wIAYMKwYBBAGSCAkCAgEBBBAMDnRhZ2dlZC1jb250ZW50MCAGDCsGAQQBkggJ\nAgIBAgQQDA50YWdnZWQtY29udGVudDAdBgwrBgEEAZIICQICAQUEDQwLdGVzdC12\nZW5kb3IwIgYMKwYBBAGSCAkCAgEGBBIMEC9mb28vcGF0aC9hbHdheXMwJgYMKwYB\nBAGSCAkCAgEHBBYMFC9mb28vcGF0aC9hbHdheXMvZ3BnMBMGDCsGAQQBkggJAgIB\nCAQDDAExMBsGDCsGAQQBkggJAgIBCgQLDAlUQUcxLFRBRzIwFQYMKwYBBAGSCAkC\niFcBBAUMA3l1bTAaBg0rBgEEAZIICQKIVwEBBAkMB2NvbnRlbnQwIAYNKwYBBAGS\nCAkCiFcBAgQPDA1jb250ZW50LWxhYmVsMB4GDSsGAQQBkggJAohXAQUEDQwLdGVz\ndC12ZW5kb3IwHAYNKwYBBAGSCAkCiFcBBgQLDAkvZm9vL3BhdGgwIQYNKwYBBAGS\nCAkCiFcBBwQQDA4vZm9vL3BhdGgvZ3BnLzAUBg0rBgEEAZIICQKIVwEIBAMMATEw\nFAYNKwYBBAGSCAkCiFcBCQQDDAEwMBwGCisGAQQBkggJBAEEDgwMUkhJQyBQcm9k\ndWN0MBQGCisGAQQBkggJBAIEBgwEMTIzNDAUBgorBgEEAZIICQQDBAYMBHJoaWMw\nEQYKKwYBBAGSCAkEBQQDDAExMCQGCisGAQQBkggJBAYEFgwUMjAxMi0wOC0yOFQy\nMjo0NzoyOFowJAYKKwYBBAGSCAkEBwQWDBQyMDEyLTA4LTI4VDIzOjQ3OjI4WjAR\nBgorBgEEAZIICQQMBAMMATAwEQYKKwYBBAGSCAkEDgQDDAEwMA0GCSqGSIb3DQEB\nBQUAA4GBAEbBBIl7zchyJ/iZ+8kc/xFXd3x0sKfnqzUTIGQYfH14Xo4tjYB0bymv\ngpXxM1+5zxwI5aiiIuvccrOgomZQIV8LHowxig+NmZb/PDCqfYw/32knReoi2bVG\nq2jpdUJLV9QdTm7KR5Lh7pPJb4foMKWEJrpztaXdMR4rfXw4Gzpe\n-----END CERTIFICATE-----\n"
        self.expected_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEAgJ5Cz8jQ+twjG6sOMM4HXuDLXlGWNNBV1N5TX/NVIUQ9Bzkg\njzv1FTkpNUasASHXTjzVc7rlBmrXA4WN4y/y/gCHKsi4DEnjVNUq9j4aJ4NjAVLr\ntvh5OVIrWHZBKfcJFy06De0pcZWT6pUhUtW9ZqpqajRYefRUxjaiTtDNUq4rpzgL\nwYuAprzULd19cwpQEiY1TWlqoVQoJy4/3q9YVvLwXquXOohdE+5iS6j/RFf7arUi\nJptkwyCXS7+YyPAlJDo6qnNWvxBLY0n2ApKGpFdgnZAq/01DIXJaNETduqdTX4w3\nVDgdKf4dzDq5FnnEktWHKZEkyKru81IiHTfH/wIDAQABAoIBAD7XlMNbVihL6Od6\n43sbH2TPJu6VpHN3m4hffJM0HFMduUfPNMZnQC83d5ftSNtgwocamBxso7xH9Xhm\nB9aKNgq/DUvtOGfgri9j3BLmcvb9biFWd481xl0odb9KQDqV1h453dSyHP6/W79R\nUC/d+SWxfD8aBmTH6afTR+iEgt2zRAQheBEsO0TKd+j3d18ijkgPx2dZyzZIRWYD\nPNEVdpFu0ECZ8PmFU14UkslZoHuD3xTy2lT2sbfJNYb7L0/72glfDvDiyz8lCl4m\ng+DRvre/a/JlxO/4ZzHAsOjrOnVJ1MYj0JpnuTVfhPYdn1vu8AUaKUaejfjBYD6Z\n9XmQ+OkCgYEAxI4HyLMGpHP6Q5XZ5NB2gvuxIyLoX7y2pLks54bsvriR6Qt0FtPA\nYV9ukYUen2+TFCAHl0XbwjKDYyX3h+FWQ07aRVVOZzsTtYA+av6c7ppnpOrFXJWS\n6oJFWL4FQuOo+Fxhqsleo/sg7tXvoxm0hHjxJRzD+mA3RGmbJFkq48UCgYEAp4RW\nnHcEGeK3+WKzt8s3G0ujTxO3qowyi9BeHA1DR0YGpHd0mdI0TAqF9u1YADBSfmj0\nXaMXw4PzctdGfBbI6kYwI6N+tzN2EdYFx1E1KfSCaEpkGFOajLr3a2lYBI7tMsJO\n3PvcWLk9RxfZwad/ADkFsbIL3SDVAJXt3dzQhPMCgYEArc8u4PI2wHvyZYuAmA8j\njWZGWNzIgchd9kHtjHtKpMiP9nVzXbA4YaLDIpmF39UJSXWdYM6cqxiCCM4NGrJP\n1stGxqLN5wldv1U9XN30JiaR2krk5Z86wHccHYJDIsgwphcDIsRZFUa/85NpCmBz\nueU80OWkA6bLmIqOb1EOVUUCgYA5gaLB/9F2mXASuqF7fNWkFyku4lPwxkQr3xIP\nizYHZ7CsER4EGDc/y3UFuaC2H+CR6LHK20wzID8Ys3JM8v1x/zpTYbMEbTQhF1nQ\nfL5Fcty5tJ/8AedSXHTHeNhwaChhfnbYQdX4106D81obssZUaz7bK4YLGVRF6TJJ\nMZ6bpQKBgQC5VyoVIrRr+w0x2ZTcJ5xPj/9L+/gS2l1o5BvzNLq6puYgz9BkMwW+\nfVpRRyaTS4BPy14qH2DqHXcqWmsfLw9Zz75wUQexkPbweFiHWB4FS2CbFHoY3w/m\ney4+0iP9HgM6TLZyuSagPkpVW/cC5i0d+STzjcsGhUeqkHIm6v4i3w==\n-----END RSA PRIVATE KEY-----\n"
        self.expected_serial = 2494424654876837057
        self.checkin = CheckIn()
        self.valid_products = ["40", "41"]
        self.valid_identity_uuid = self.checkin.extract_id_from_identity_cert(self.valid_identity_cert_pem)
        self.expected_valid_identity_uuid = "98e6aa41-a25d-4d60-976b-d70518382683"
        self.load_rhic_data()

    def load_rhic_data(self):
        create_new_consumer_identity(self.valid_identity_uuid, self.valid_products)

    def tearDown(self):
        super(BaseEntitlementTestCase, self).tearDown()
        candlepin_client._request = self.saved_candlepin_client_request_method
        rhic_serve_client._request = self.saved_rhic_serve_client_request_method

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

    def tearDown(self):
        super(EntitlementResourceTest, self).tearDown()

    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

    def test_put_entitlement_valid_identity(self):
        resp = self.api_client.put('/api/v1/entitlement/BOGUS_IDENTITY/', format='json',
            authentication=self.get_credentials(), data=self.post_data,
            SSL_CLIENT_CERT=self.valid_identity_cert_pem)
        self.assertHttpAccepted(resp)
        self.assertTrue(resp['Content-Type'].startswith('application/json'))
        self.assertValidJSON(resp.content)

        deserialized = self.deserialize(resp)
        self.assertEquals(len(deserialized["certs"]), 1)
        self.assertEquals(deserialized["certs"][0][0], self.expected_cert)
        self.assertEquals(deserialized["certs"][0][1], self.expected_key)
        self.assertEquals(deserialized["certs"][0][2], self.expected_serial)

    def test_put_entitlement_invalid_identity(self):
        resp = self.api_client.put('/api/v1/entitlement/BOGUS_IDENTITY/',
            format='json',
            authentication=self.get_credentials(),
            data=self.post_data,
            SSL_CLIENT_CERT=self.invalid_identity_cert_pem)
        self.assertHttpForbidden(resp)
        self.assertEqual("Unable to verify consumer's identity certificate was signed by configured CA", resp.content)

class CandlepinClientTest(BaseEntitlementTestCase):

    def setUp(self):
        super(CandlepinClientTest, self).setUp()

    def tearDown(self):
        super(CandlepinClientTest, self).tearDown()

    def test_get_entitlement(self):
        cert_info = candlepin_client.get_entitlement(host="localhost", port=0, url="mocked",
            installed_products=[4], identity="dummy identity", username="", password="")
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

class IdentityTest(BaseEntitlementTestCase):
    def setUp(self):
        super(IdentityTest, self).setUp()

    def tearDown(self):
        super(IdentityTest, self).tearDown()

    def test_get_all_rhics(self):
        rhics = rhic_serve_client.get_all_rhics(host="localhost", port=0, url="mocked")
        self.assertEquals(len(rhics), 3)

    def test_sync_from_rhic_serve_blocking(self):
        self.drop_database_and_reconnect()
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 0)
        sync_from_rhic_serve_blocking()
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 3)
        expected_rhics = ["480ed55f-c3fb-4249-ac4c-52e440cd9304",
                          "c921d17e-cf82-4738-bfbb-36a83dc45c03",
                          "98e6aa41-a25d-4d60-976b-d70518382683"]
        for r in rhics:
            self.assertTrue(r.uuid in expected_rhics)

    def test_sync_from_rhic_serve_threaded(self):
        self.drop_database_and_reconnect()
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 0)
        sync_thread = sync_from_rhic_serve()
        for index in range(0,60):
            if not sync_thread.finished:
                time.sleep(.05)
        self.assertTrue(sync_thread.finished)
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 3)
        expected_rhics = ["480ed55f-c3fb-4249-ac4c-52e440cd9304",
                          "c921d17e-cf82-4738-bfbb-36a83dc45c03",
                          "98e6aa41-a25d-4d60-976b-d70518382683"]
        for r in rhics:
            self.assertTrue(r.uuid in expected_rhics)

    def test_sync_that_removes_old_rhics(self):
        self.drop_database_and_reconnect()
        # Create one dummy RHIC which our sync should remove
        create_new_consumer_identity("old rhic uuid to be removed", ["1","2"])
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 1)
        sync_from_rhic_serve_blocking()
        rhics = ConsumerIdentity.objects()
        self.assertEquals(len(rhics), 3)
        expected_rhics = ["480ed55f-c3fb-4249-ac4c-52e440cd9304",
                          "c921d17e-cf82-4738-bfbb-36a83dc45c03",
                          "98e6aa41-a25d-4d60-976b-d70518382683"]
        for r in rhics:
            self.assertTrue(r.uuid in expected_rhics)

class CheckInTest(BaseEntitlementTestCase):
    """
    Tests to exercise splice.entitlement.checkin.CheckIn
    """
    def setUp(self):
        super(CheckInTest, self).setUp()

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
            "98e6aa41-a25d-4d60-976b-d70518382683")

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
