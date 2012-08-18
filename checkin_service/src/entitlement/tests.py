from tastypie.test import ResourceTestCase

from mongoengine import connect
from django.conf import settings

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

class EntitlementResourceTest(MongoTestCase):

    def setUp(self):
        super(EntitlementResourceTest, self).setUp()
        self.username = "admin"
        self.password = "admin"
        # TODO add auth
        # self.user = User.objects.create_user(self.username, 'admin@example.com', self.password)
        self.post_data = {
            'identity_cert': "X509 Cert Contents will go here",
            'products': ["Product_1", "Product_2"],
        }

    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

    def test_put_entitlement(self):
        resp = self.api_client.put('/api/v1/entitlement/BOGUS_IDENTITY/', format='json',
            authentication=self.get_credentials(), data=self.post_data)

        self.assertHttpAccepted(resp)
        self.assertTrue(resp['Content-Type'].startswith('application/json'))
        self.assertValidJSON(resp.content)

        deserialized = self.deserialize(resp)
        self.assertTrue("entitlement" in deserialized)
        self.assertTrue("message" in deserialized)
        self.assertTrue(deserialized["entitlement"])
        self.assertFalse(deserialized["message"])

