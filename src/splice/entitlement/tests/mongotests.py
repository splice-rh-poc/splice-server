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

from datetime import datetime
from dateutil.tz import tzutc
import time

from mongoengine import signals, Document, StringField

from base import MongoTestCase

from splice.common.fields import IsoDateTimeField
from splice.common import utils

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

    def test_datetime_offset_aware(self):
        """
        Test to address
          TypeError: can't compare offset-naive and offset-aware datetimes
        """
        def get_now():
            return datetime.now(tzutc())
        class OffsetTest(Document):
            uuid = StringField(required=True, unique=True)
            stamp = IsoDateTimeField(required=True, default=get_now)
            @classmethod
            def pre_save(cls, sender, document, **kwargs):
                if isinstance(document.stamp, basestring):
                    document.stamp = utils.convert_to_datetime(document.stamp)

            def __str__(self):
                msg = "%s with stamp of %s" % (self.__class__, self.stamp)
                return msg

        signals.pre_save.connect(OffsetTest.pre_save, sender=OffsetTest)
        a = OffsetTest(uuid="a")
        a.save()
        found = OffsetTest.objects(uuid=a.uuid).first()
        self.assertIsNotNone(found)

        time.sleep(1)
        b = OffsetTest(uuid="b")
        self.assertTrue(b.stamp > a.stamp)

        # Create an instance that has it's date field initialy a string without a timezone
        #  we want the conversion to assume a UTC timezone
        #  save this object to mongo
        #  query the object from mongo and ensure the timezone info has been set
        #  Note:  Fix for this is to ensure that 'tz_aware=True' is passed into mongo
        obj_with_date_from_str = OffsetTest(uuid="obj_with_date_from_str", stamp="2011-12-01T11:13:06.432367")
        obj_with_date_from_str.save()
        self.assertIsNotNone(obj_with_date_from_str.stamp.tzinfo)
        found = OffsetTest.objects(uuid=obj_with_date_from_str.uuid).first()
        self.assertIsNotNone(found.stamp.tzinfo)

        self.assertTrue(b.stamp > obj_with_date_from_str.stamp)
