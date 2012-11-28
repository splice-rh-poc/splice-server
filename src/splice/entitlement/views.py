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
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

_LOG = logging.getLogger(__name__)

@csrf_exempt
def bad_identity_certificate(request):
    """
    Responsible for returning an error message and a '500' informing
    clients server is unable to process requests
    @return:
    """
    _LOG.error("Server's identity certificate is invalid.  Unable to process request: %s" % (request.get_full_path()))
    return HttpResponse(
            content= "Invalid Server Identity certificate. All services halted.",
            status=500)

