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

from datetime import datetime, date
import isodate

from mongoengine import DateTimeField

class IsoDateTimeField(DateTimeField):

    def prepare_query_value(self, op, value):

        # If value is a string, try to parse it as a datetime.datetime or
        # datetime.date.
        if isinstance(value, basestring):
            try:
                value = isodate.parse_datetime(value)
            except (ValueError, isodate.ISO8601Error):
                try:
                    value = isodate.parse_date(value)
                except (ValueError, isodate.ISO8601Error):
                    value = None

        if value is None:
            return value

        # Ensure timezone info is set, if not, default to UTC.
        if isinstance(value, datetime):
            if not value.tzinfo:
                value.replace(tzinfo=isodate.UTC)
            return value

        # Assume default time of 00:00, and default timezone of UTC on just a
        # datetime.date object.
        if isinstance(value, date):
            # This will assume time is 00:00
            value = datetime.fromordinal(value.toordinal())
            # Assume UTC
            value.replace(tzinfo=isodate.UTC)
            return value


        
