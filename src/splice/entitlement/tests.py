import json
import os

from tastypie.test import ResourceTestCase

from mongoengine.connection import connect, disconnect
from django.conf import settings

from splice.common import candlepin_client
from splice.common.certs import CertUtils
from splice.common.identity import create_new_consumer_identity
from splice.entitlement.checkin import CheckIn, CertValidationException
from splice.entitlement.models import ConsumerIdentity

TEST_DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "test_data")

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

def mocked_request_method(host, port, url, installed_product,
                          identity, username, password, debug=False):
    example_data = os.path.join(TEST_DATA_DIR, "example_candlepin_data.json")
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
        self.saved_request_method = candlepin_client._request
        candlepin_client._request = mocked_request_method
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
        self.expected_cert = "-----BEGIN CERTIFICATE-----\nMIID3zCCA0igAwIBAgICBNIwDQYJKoZIhvcNAQEFBQAwODEXMBUGA1UEAwwOaXAt\nMTAtNi05NC0xNDExCzAJBgNVBAYTAlVTMRAwDgYDVQQHDAdSYWxlaWdoMB4XDTEy\nMDgyNzE5NTc1NVoXDTEyMDgyNzIwNTc1NVowFzEVMBMGA1UEAxMMdGVzdHRlc3R0\nZXN0MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsKDEY3dK0uc0ImSt\nSlQMfQzuR/iQgC3mHLapYPdqHRvX6w4PXx8uOKz1yMjuLj0/0GHtCod97VfAtL/h\nJ/FH9mMsR18y6qezcgbWKU4M4lffH3auQoCFUiJNlEi94d0qxH6iKyWqKRHveRa3\nerILvhMQG6np6XDt3gWirpRwZzi21qr5ZYh83brsuxzU6HfYB51jBYs0uJybxIfm\nDrpRa3YQiyPtE72v8IIcvqYDoXq9QzOVqAMOiw5BLpc0pKQVN6KeB8BYXEa5sfr/\nuQr+GhvlXWS/YWRZiqj6aW56vAKK+arvEbRKFkybJbnSNrfCt8ZKLrB7mZGbxySd\n1xvu7wIDAQABo4IBkzCCAY8wEQYJYIZIAYb4QgEBBAQDAgWgMAsGA1UdDwQEAwIE\nsDBoBgNVHSMEYTBfgBSl9RwXEephltcl32HNuZwR7ZAm16E8pDowODEXMBUGA1UE\nAwwOaXAtMTAtNi05NC0xNDExCzAJBgNVBAYTAlVTMRAwDgYDVQQHDAdSYWxlaWdo\nggkA0hXeS2SIlPMwHQYDVR0OBBYEFL6EQZpQ/Nm3DLW7ZM9UqMxv8VNpMBMGA1Ud\nJQQMMAoGCCsGAQUFBwMCMBwGCisGAQQBkggJBAEEDgwMUkhJQyBQcm9kdWN0MBYG\nCisGAQQBkggJBAIECAwGU1VCLUlEMBQGCisGAQQBkggJBAMEBgwEcmhpYzARBgor\nBgEEAZIICQQFBAMMATEwJAYKKwYBBAGSCAkEBgQWDBQyMDEyLTA4LTI3VDE5OjU3\nOjU1WjAkBgorBgEEAZIICQQHBBYMFDIwMTItMDgtMjdUMjA6NTc6NTVaMBEGCisG\nAQQBkggJBAwEAwwBMDARBgorBgEEAZIICQQOBAMMATAwDQYJKoZIhvcNAQEFBQAD\ngYEALdvvPEU3ozYse4NCSz+B3VrSrZ9Dv6vD+9yRqpXF/AWeYUgO4uyVc5fKzQDZ\nQTRXfqnvyJ773JOTUxJlYHt7uK2wGHbRefsRktGzLnwo3KZOhHWUXtMdt9bNzHw2\nt1rG3Jeubsw5v1s/Dhp5wHR0RvzrHnkxTVI/XFXbqnPvDJ0=\n-----END CERTIFICATE-----\n"
        self.expected_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAsKDEY3dK0uc0ImStSlQMfQzuR/iQgC3mHLapYPdqHRvX6w4P\nXx8uOKz1yMjuLj0/0GHtCod97VfAtL/hJ/FH9mMsR18y6qezcgbWKU4M4lffH3au\nQoCFUiJNlEi94d0qxH6iKyWqKRHveRa3erILvhMQG6np6XDt3gWirpRwZzi21qr5\nZYh83brsuxzU6HfYB51jBYs0uJybxIfmDrpRa3YQiyPtE72v8IIcvqYDoXq9QzOV\nqAMOiw5BLpc0pKQVN6KeB8BYXEa5sfr/uQr+GhvlXWS/YWRZiqj6aW56vAKK+arv\nEbRKFkybJbnSNrfCt8ZKLrB7mZGbxySd1xvu7wIDAQABAoIBAGp7oaotguh/Bokt\nlONYpGbHYuf0zHjaMv5giOCyiECgRp2ozk+UZrM4Yrz3ldA+kLg6MUPFx39NBhpy\nC3WfGrlJtKoalIGvNJmr0XT5Xv8d5p/7Vrc08CtCDu80o3UFdwEbLv1AKcO00mB3\n94l6yWV/7Jgg6aoYsO7HCvqg9tri76Lc/ALblMfJ04oEvjHo3bo3OcQ5WQT/fhM+\nI1eIqulA1aPP79Wjta/KkeQ/WmKmvqz+eh9ukHdQQNdL1Hxa3sL0HgKbKknBQm2i\nKdPHLJGmc8yqv/0oJL8VZYYvtEOl/XOBZujJqI7WryA4YC9AJc0xjXP6DxrxrLOJ\n4MBChPECgYEA22RTQdjrmEWY/wRiqv0yPMJ0X81qUcpWFnwKQuZJf6811bi0hfej\n6o0h8H4x5PjVSWOTOirX6oI9mHUr5xERlt2YCuoTd/YDeXTSY68o1hKUwQm0RsV6\nN1mIoJ6D/qyuRp5BGKhhOJa5qB3Jbiwb7XEwg/181OXKi3VBG4lAkrMCgYEAzhm2\nuY8T4ep37VoYpQKJ91xm6qctfLxhiFzSWEjTFSJhYqp8cQn2HOovD692jUmczPDQ\nr6634ueSPF2+oRGFv3UlMtqKmEqCDD4dHl11+Xnry8kXjb7Pxq6oJDlRBjRMf2Mu\n4rHxDXpX9hv9S4nzwFoDr6JSYd8ygcqvtgWGoNUCgYEAwCYrQVWyaigyqs/1dtrR\ngCOzdyDbCI2VPpYfCp7VKq6TEP93pInTF5/KZO6x1mAVtfQvQ1e4ydyOBBRDgloR\ntLeZ7Z07tepS+rJVfhcwReX6QOO17/IPa6DQKBUNeCVXceQzEVyP4dco/dQw0nxx\nbVGgc0m1ZmVoMyJcBrj8RD8CgYBgtXAoYhrSR1M+7Kfjxe03RQSF1yxg+4RImEWb\nZ5Ckuh04TwdVg3cY2kp68bqPUZtiDx3dUf63WjIkYVix+6bmz/FEi4e9LjkXxY2k\nUfapuawLU7DZsk+Myyfa14pNfvzmSYQWm6igyme79CZG69SUzagtId3GTxVEEfeh\nUbZ6gQKBgERwlTIEZ6th8elckNl/Zso1g262xPy7GwX8IFlDCvY9ZAfoRz+aBWHK\nK4UbqPZmwXMsQJO7WVOdHoSl7pRPuS0196TEyYw3gu2rVAFernojX1EM0Q0eakYn\nPO75QiHsxdlIsfg1eNEXKqflCivXd3fDXuBtT/Q2MJBmE2ZkxTOB\n-----END RSA PRIVATE KEY-----\n"
        self.checkin = CheckIn()
        self.valid_products = ["40", "41"]
        self.valid_identity_uuid = self.checkin.extract_id_from_identity_cert(self.valid_identity_cert_pem)
        self.load_rhic_data()

    def load_rhic_data(self):
        create_new_consumer_identity(self.valid_identity_uuid, self.valid_products)

    def tearDown(self):
        super(BaseEntitlementTestCase, self).tearDown()
        candlepin_client._request = self.saved_request_method

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

    def test_put_entitlement_invalid_identity(self):
        caught = False
        try:
            self.api_client.put('/api/v1/entitlement/BOGUS_IDENTITY/',
                format='json',
                authentication=self.get_credentials(),
                data=self.post_data,
                SSL_CLIENT_CERT=self.invalid_identity_cert_pem)
        except CertValidationException, e:
            caught = True
        self.assertTrue(caught)

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

    def test_parse_cert_subject(self):
        self.assertEquals(self.checkin.parse_cert_subject("/OU=foo/CN=bar", "CN"), "bar")
        self.assertEquals(self.checkin.parse_cert_subject("/OU=foo/CN=bar/EM=baz", "CN"), "bar")
        self.assertEquals(self.checkin.parse_cert_subject("/OU=foo/EM=baz", "CN"), None)

    def test_extract_id_from_identity_cert(self):
        # below is example of subject from test data
        # $ openssl x509 -subject -in test_data/valid_cert/sample_rhic_valid.pem
        #        subject=/CN=dbcbc8e1-5b37-4a77-9db1-faf4ef29307d
        self.assertEquals(
            self.checkin.extract_id_from_identity_cert(self.valid_identity_cert_pem),
            "dbcbc8e1-5b37-4a77-9db1-faf4ef29307d")

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