import json
import os

from tastypie.test import ResourceTestCase

from mongoengine import connect
from django.conf import settings

from splice.common import candlepin_client
from splice.common.certs import CertUtils
from splice.entitlement.checkin import CheckIn, CertValidationException

TEST_DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "test_data")

# Adapted From:
# https://github.com/vandersonmota/mongoengine_django_tests/blob/master/mongotest.py
class MongoTestCase(ResourceTestCase):
    """
    TestCase class that clear the collection between the tests
    """
    db_name = 'test_%s' % settings.MONGO_DATABASE_NAME
    def __init__(self, methodName='runtest'):
        self.db = connect(self.db_name)
        super(MongoTestCase, self).__init__(methodName)

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
        self.post_data_invalid_identity = {
            'identity_cert': self.invalid_identity_cert_pem,
            'consumer_identifier': "52:54:00:15:E7:69",
            'products': ["Product_1", "Product_2"],
            }
        self.post_data_valid_identity = {
            'identity_cert': self.valid_identity_cert_pem,
            'consumer_identifier': "52:54:00:15:E7:69",
            'products': ["Product_1", "Product_2"],
        }

    def tearDown(self):
        super(EntitlementResourceTest, self).tearDown()

    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

    def test_put_entitlement_valid_identity(self):
        resp = self.api_client.put('/api/v1/entitlement/BOGUS_IDENTITY/', format='json',
            authentication=self.get_credentials(), data=self.post_data_valid_identity)
        self.assertHttpAccepted(resp)
        self.assertTrue(resp['Content-Type'].startswith('application/json'))
        self.assertValidJSON(resp.content)

        deserialized = self.deserialize(resp)
        self.assertEquals(deserialized["product_id"], "awesomeos-virt-4")
        self.assertEquals(deserialized["product_name"], "Awesome OS with up to 4 virtual guests")
        self.assertEquals(len(deserialized["certs"]), 1)

    def test_put_entitlement_invalid_identity(self):
        caught = False
        try:
            self.api_client.put('/api/v1/entitlement/BOGUS_IDENTITY/',
                format='json',
                authentication=self.get_credentials(),
                data=self.post_data_invalid_identity)
        except CertValidationException, e:
            caught = True
        self.assertTrue(caught)

class CandlepinClientTest(BaseEntitlementTestCase):

    def setUp(self):
        super(CandlepinClientTest, self).setUp()

    def tearDown(self):
        super(CandlepinClientTest, self).tearDown()

    def test_get_entitlement(self):
        product_info = candlepin_client.get_entitlement(host="localhost", port=0, url="mocked",
            installed_product=[4], identity="dummy identity", username="", password="")
        self.assertEquals(len(product_info), 1)
        self.assertEquals(product_info[0]["product_id"], u"awesomeos-virt-4")
        self.assertEquals(product_info[0]["product_name"], u'Awesome OS with up to 4 virtual guests')
        cert_info = product_info[0]["certs"]
        self.assertEquals(len(cert_info), 1)
        self.assertTrue(cert_info[0].has_key("cert"))
        self.assertTrue(cert_info[0].has_key("key"))


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
        self.checkin = CheckIn()

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


