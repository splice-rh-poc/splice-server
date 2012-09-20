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

import httplib
from django.http import HttpResponse

class CheckinException(Exception):
    pass

class CertValidationException(CheckinException):
    def __init__(self):
        self.response = HttpResponse(
            content="Unable to verify consumer's identity certificate was signed by configured CA",
            status=httplib.FORBIDDEN)

class UnallowedProductException(CheckinException):
    def __init__(self, consumer_uuid, products):
        super(UnallowedProductException, self).__init__(self, )
        self.consumer_uuid = consumer_uuid
        self.products = products
        self.response = HttpResponse(
            content= self.__str__(),
            status=httplib.PAYMENT_REQUIRED
        )

    def __str__(self):
        return "Consumer with uuid '%s' is not allowed to access products '%s'" % (self.consumer_uuid, self.products)

class UnknownConsumerIdentity(CheckinException):
    def __init__(self, identity):
        super(UnknownConsumerIdentity, self).__init__(self)
        self.identity = identity
        self.response = HttpResponse(
            content=self.__str__(),
            # status = httplib.NOT_FOUND
            # For a quick work around to aid in submgr testing
            # we are returning a 202 for now
            # TODO: Revisit later and update, a diff exception should prob be
            # thrown in checkin.py
            status=httplib.ACCEPTED
        )

    def __str__(self):
        return "Unknown consumer identity '%s'" % (self.identity)

class RequestException(Exception):
    """
    This exception is to be used when this server is sending a remote request
    to a service and encounters an error.
    """
    def __init__(self, status, message=""):
        super(RequestException, self).__init__()
        self.status = status
        self.message = message
        self.response = HttpResponse(
            content=self.__str__(),
            # status is marking a remote service had a problem
            status=httplib.BAD_GATEWAY
        )

    def __str__(self):
        return "Exception: remote request yielded status code: '%s' with body '%s'"\
        % (self.status, self.message)

class UnsupportedDateFormatException(Exception):
    def __init__(self, date_str, message=""):
        super(UnsupportedDateFormatException, self).__init__()
        self.date_str = date_str
        self.message = message
        self.response = HttpResponse(
            content=self.__str__(),
            status=httplib.BAD_REQUEST
        )

    def __str__(self):
        return "Exception: datetime string of '%s' could not be parsed with any known methods." \
               % (self.date_str)