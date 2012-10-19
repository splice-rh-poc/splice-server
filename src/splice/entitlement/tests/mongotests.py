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

from mongoengine import Document, StringField

from base import MongoTestCase

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
