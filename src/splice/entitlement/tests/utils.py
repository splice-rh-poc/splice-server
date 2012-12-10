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

import logging

from splice.common import utils
from splice.common.exceptions import UnsupportedDateFormatException

# Unit test imports
from base import BaseEntitlementTestCase

LOG = logging.getLogger(__name__)

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
        self.assertIsNotNone(dt_a.tzinfo)

        b = '2012-09-19T19:01:55+00:00'
        dt_b = utils.convert_to_datetime(b)
        self.assertEquals(dt_b.year, 2012)
        self.assertEquals(dt_b.month, 9)
        self.assertEquals(dt_b.day, 19)
        self.assertEquals(dt_b.hour, 19)
        self.assertEquals(dt_b.minute, 1)
        self.assertEquals(dt_b.second, 55)
        self.assertIsNotNone(dt_b.tzinfo)

        c = '2012-09-19T19:01:55'
        dt_c = utils.convert_to_datetime(c)
        self.assertEquals(dt_c.year, 2012)
        self.assertEquals(dt_c.month, 9)
        self.assertEquals(dt_c.day, 19)
        self.assertEquals(dt_c.hour, 19)
        self.assertEquals(dt_c.minute, 1)
        self.assertEquals(dt_c.second, 55)
        self.assertIsNotNone(dt_c.tzinfo)

        d = '2012-12-06T10:11:48.050566'
        dt_d = utils.convert_to_datetime(d)
        self.assertEquals(dt_d.year, 2012)
        self.assertEquals(dt_d.month, 12)
        self.assertEquals(dt_d.day, 06)
        self.assertEquals(dt_d.hour, 10)
        self.assertEquals(dt_d.minute, 11)
        self.assertEquals(dt_d.second, 48)
        self.assertIsNotNone(dt_d.tzinfo)

        caught  = False
        bad_value = 'BadValue'
        try:
            utils.convert_to_datetime(bad_value)
            self.assertTrue(False) # Exception should be raised
        except UnsupportedDateFormatException, e:
            caught = True
            self.assertEquals(e.date_str, bad_value)
        self.assertTrue(caught)
