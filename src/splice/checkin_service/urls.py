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

import sys
import traceback

from django.conf.urls import patterns, include, url
from django.core.signals import got_request_exception
from tastypie.api import Api

from splice.entitlement import on_startup
on_startup.run()

from splice.entitlement.apis import EntitlementResource, RHICRCSModifiedResource, ModifiedProductUsageResource



v1_api = Api(api_name='v1')
v1_api.register(EntitlementResource())
v1_api.register(RHICRCSModifiedResource())
v1_api.register(ModifiedProductUsageResource())

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'checkin_service.views.home', name='home'),
    # url(r'^checkin_service/', include('checkin_service.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    (r'^api/', include(v1_api.urls)),
)



# Print all exceptions to apache error log
def exception_printer(sender, **kwargs):
    print >> sys.stderr, ''.join(traceback.format_exception(*sys.exc_info()))

got_request_exception.connect(exception_printer)
