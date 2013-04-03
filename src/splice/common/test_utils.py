# Copyright  2013 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

from django.conf import settings
from mongoengine.connection import connect, disconnect, register_connection
from mongoengine.queryset import QuerySet
from tastypie.test import ResourceTestCase, TestApiClient

class RawTestApiClient(TestApiClient):
    """
    Will not serialize passed in 'data'
    Assumes caller is responsible for all serialization outside of this test code
    """
    def post(self, uri, format='json', data=None, authentication=None, **kwargs):
        content_type = self.get_content_type(format)
        kwargs['content_type'] = content_type

        if data is not None:
            kwargs['data'] = data

        if authentication is not None:
            kwargs['HTTP_AUTHORIZATION'] = authentication

        return self.client.post(uri, **kwargs)

    def put(self, uri, format='json', data=None, authentication=None, **kwargs):
        content_type = self.get_content_type(format)
        kwargs['content_type'] = content_type

        if data is not None:
            kwargs['data'] = data

        if authentication is not None:
            kwargs['HTTP_AUTHORIZATION'] = authentication

        return self.client.put(uri, **kwargs)


class ModifiedResourceTestCase(ResourceTestCase):
    """
    A useful base class for the start of testing Tastypie APIs.
    """
    def setUp(self):
        # Overriding the default serializer to use our MongoEncoder
        super(ModifiedResourceTestCase, self).setUp()
        self.raw_api_client = RawTestApiClient(self.serializer)


# Adapted From:
# https://github.com/vandersonmota/mongoengine_django_tests/blob/master/mongotest.py
class MongoTestCase(ModifiedResourceTestCase):
    """
    TestCase class that clear the collection between the tests
    """
    db_name = 'test_%s' % settings.MONGO_DATABASE_NAME
    def __init__(self, methodName='runtest'):
        super(MongoTestCase, self).__init__(methodName)
        disconnect()
        self.db = connect(self.db_name, tz_aware=True)
        self.drop_database_and_reconnect()

    def _post_teardown(self):
        super(MongoTestCase, self)._post_teardown()
        self.drop_database_and_reconnect(reconnect=False)

    def drop_database_and_reconnect(self, reconnect=True):
        disconnect()
        disconnect('rhic_serve')
        self.db.drop_database(self.db_name)
        # Mongoengine sometimes doesn't recreate unique indexes
        # in between test runs, adding the below 'reset' to fix this
        # https://github.com/hmarr/mongoengine/issues/422
        QuerySet._reset_already_indexed()
        if reconnect:
            self.db = connect(self.db_name, tz_aware=True)
            register_connection('rhic_serve', self.db_name)

    def assertDateTimeIsEqual(self, left, right):
        self.assertEquals(left.year, right.year)
        self.assertEquals(left.month, right.month)
        self.assertEquals(left.day, right.day)
        self.assertEquals(left.hour, right.hour)
        self.assertEquals(left.minute, right.minute)
        self.assertEquals(left.second, right.second)