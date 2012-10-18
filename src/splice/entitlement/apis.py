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


from tastypie import fields
from tastypie import http
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.bundle import Bundle
from tastypie.exceptions import NotFound
from tastypie.resources import Resource
from tastypie.exceptions import NotFound, BadRequest

from rhic_serve.rhic_rcs.api import rhic
from report_server.report_import.api import productusage

from splice.common import config
from splice.entitlement.checkin import CheckIn
from splice.entitlement import tasks
from splice.common import certs
from splice.common.identity import get_current_rhic_lookup_tasks
from splice.managers import identity_lookup

import logging
_LOG = logging.getLogger(__name__)

class ModifiedProductUsageResource(productusage.ProductUsageResource):
    class Meta(productusage.ProductUsageResource.Meta):
        #
        # We want our class to have the same URL pattern as the base class
        # So...explicitly setting 'resource_name'
        #
        resource_name = 'productusage'

    def __init__(self):
        super(ModifiedProductUsageResource, self).__init__()

    def import_hook(self, product_usages):
        for pu in product_usages:
            # Need to guard against duplicate entries being imported
            #   Add a way to make a product usage to a splice server unique
            #   then when we import we
            # Need to measure performance, expect this API will receive heavy usage
            _LOG.info("importing %s" % (pu))


class RHICRCSModifiedResource(rhic.RHICRcsResource):

    class Meta(rhic.RHICRcsResource.Meta):
        #
        # We want our class to have the same URL pattern as the base class
        # So...explicitly setting 'resource_name'
        #
        resource_name = 'rhicrcs'

    def __init__(self):
        super(RHICRCSModifiedResource, self).__init__()

    def get_detail(self, request, **kwargs):
        resp = super(RHICRCSModifiedResource, self).get_detail(request, **kwargs)
        if resp.status_code == 404:
            status_code = self.handle_rhic_lookup(kwargs['uuid'])
            resp.status_code = status_code
        return resp

    def handle_rhic_lookup(self, rhic_uuid):
        """
        Will look up if an existing lookup is in progress for this RHIC.
        If a task is found, will return it's status code if completed, or 202 to signal in progress
        If a task is not found, will create a new task and return 202 to signal in progress
        @param rhic_uuid:
        @return: status code to return for request
        @rtype: int
        """
        _LOG.info("Processing rhic_lookup for an unknown RHIC of UUID '%s' " % (rhic_uuid))
        task = get_current_rhic_lookup_tasks(rhic_uuid)
        if task:
            if task.completed:
                ret_code = 404
                if task.status_code:
                    ret_code = task.status_code
                _LOG.info("Using cached value %s" % (task))
                return ret_code
            else:
                _LOG.info("Lookup task in progress: %s" % (task))
                return 202
        task = identity_lookup.create_rhic_lookup_task(rhic_uuid)
        _LOG.info("Initiated new lookup task: %s" % (task))
        return 202

###
#Note:  Adapted an example of how to create a Resource that doesn't use a Model from:
#       https://gist.github.com/794424
###
class Entitlement(object):
    certs = []
    message = "" # Holder for error messages
#
# TODO: Reconsider if PUT makes sense for 'checkin' call to serve an entitlement certificate
#    From server perspective, we are creating a new entitlement certificate
#    From client perspective, we are requesting an entitlement certificate,
#      I feel like the client is asking for the entitlement certificate,
#      opposed to saying "create this object with this data"
#
class EntitlementResource(Resource):
    certs = fields.ListField(attribute='certs')
    message = fields.CharField(attribute='message', null=True)

    class Meta:
        resource_name = 'entitlement'
        object_class = Entitlement
        list_allowed_methods = []
        detail_allowed_methods = ["post", "put"]
        always_return_data = True
        authentication = Authentication()
        authorization = Authorization()

    # To support a 'POST' on a 'detail', we need to override the tastypies 'post_detail' implementation
    # 'tastypie' by default does not implement a post_detail, so we fallback to behavior of a put
    def post_detail(self, request, **kwargs):
        resp = self.put_detail(request, **kwargs)
        return self.modify_response(resp)

    def put_detail(self, request, **kwargs):
        resp = super(EntitlementResource, self).put_detail(request, **kwargs)
        return self.modify_response(resp)

    def modify_response(self, resp):
        # Change resp code
        resp.status_code = 200
        resp['X-Entitlement-Time-Seconds'] = self.last_entitlement_call_length
        return resp

    def obj_update(self, bundle, request=None, skip_errors=False, **kwargs):
        try:
            return self.process_checkin(bundle, request, skip_errors, **kwargs)
        except Exception, e:
            _LOG.exception(e)
            raise

    def process_checkin(self, bundle, request, skip_errors, **kwargs):
        if not bundle.data.has_key("products"):
            raise BadRequest("Missing 'products'")
        if not bundle.data.has_key("consumer_identifier"):
            raise BadRequest("Missing 'consumer_identifier'")
        if not bundle.data.has_key("system_facts"):
            raise BadRequest("Missing 'system_facts'")

        minutes = None
        if bundle.data.has_key("minutes"):
            try:
                minutes = int(bundle.data["minutes"])
                if minutes < 1:
                    raise BadRequest("'minutes' with value of '%s' is less than 1" % (minutes))
            except:
                raise BadRequest("Unable to convert 'minutes' with value of '%s' to an integer" % (bundle.data["minutes"]))

        # Read the SSL identity certificate from the SSL request environment variables
        identity_cert = certs.get_client_cert_from_request(request)
        #_LOG.info("Using 'identity_cert': %s" % (identity_cert))
        products = bundle.data["products"]
        consumer_identifier = bundle.data["consumer_identifier"]
        system_facts = bundle.data["system_facts"]
        checkin = CheckIn()
        bundle.obj = Entitlement()
        cert_info, ent_call_time = checkin.get_entitlement_certificate(identity_cert,
            consumer_identifier, system_facts, products,
            cert_length_in_min=minutes)
        bundle.obj.certs = cert_info
        # Setting time of last entitlement call, to be inserted in response header later in processing
        self.last_entitlement_call_length = ent_call_time
        return bundle
