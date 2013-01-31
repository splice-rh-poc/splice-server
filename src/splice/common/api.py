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

from tastypie.authorization import Authorization
from tastypie_mongoengine.resources import MongoEngineResource

from splice.common import certs, utils
from splice.common.auth import X509CertificateAuthentication
from splice.common.models import SpliceServer

_LOG = logging.getLogger(__name__)

class SpliceServerResource(MongoEngineResource):

    class Meta:
        queryset = SpliceServer.objects.all()
        authorization = Authorization()
        authentication = X509CertificateAuthentication(verification_ca=certs.get_splice_server_identity_ca_pem())
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get']

    def hydrate_created(self, bundle):
        _LOG.debug("SpliceServerResource:hydrate_created bundle.data['created'] = '%s'" % (bundle.data["created"]))
        bundle.data["created"] = utils.convert_to_datetime(bundle.data["created"])
        _LOG.debug("SpliceServerResource:hydrate_created translated to bundle.data['created'] = '%s'" % (bundle.data["created"]))
        return bundle

    def hydrate_modified(self, bundle):
        _LOG.debug("SpliceServerResource:hydrate_created bundle.data['modified'] = '%s'" % (bundle.data["modified"]))
        bundle.data["modified"] = utils.convert_to_datetime(bundle.data["modified"])
        _LOG.debug("SpliceServerResource:hydrate_created translated to bundle.data['modified'] = '%s'" % (bundle.data["modified"]))
        return bundle

    def post_list(self, request, **kwargs):
        # Changing behavior so post to a list will update the collection opposed to
        # only working on a single item.
        # Note:  tastypie uses 'put_list' to update a collection
        #                      'post_list' to update a single element of a collection
        #
        # Further...'put_list' defaults to deleting the existing items in a collection before adding the new items
        super(SpliceServerResource, self).put_list(request, **kwargs)

    def obj_delete_list(self, request=None, **kwargs):
        # We are intentionally changing the tastypie default behavior of
        # deleting the entire collection on each collection 'PUT'
        pass

    def obj_create(self, bundle, request=None, **kwargs):
        bundle.obj = self._meta.object_class()

        for key, value in kwargs.items():
            setattr(bundle.obj, key, value)
        bundle = self.full_hydrate(bundle)
        self.is_valid(bundle,request)

        if bundle.errors:
            self.error_response(bundle.errors, request)

        # Our change to ignore older objects and only save if this object is "new" or "newer"
        existing = SpliceServer.objects(uuid=bundle.obj.uuid).first()
        if existing:
            _LOG.info("SpliceServerResource:obj_create()  bundle.obj.modified = '%s', existing.modified = '%s'" % \
                      (bundle.obj.modified, existing.modified))
            if bundle.obj.modified > existing.modified:
                # Request's object is newer than what's in our DB
                for key, value in bundle.obj._data.items():
                    if key:
                        # Skip the 'None' which is part of the data sent if the obj has not been saved previously
                        setattr(existing, key, value)
                existing.save()
            else:
                _LOG.debug("Ignorning %s since it is not newer than what is in DB" % (bundle.obj))
        else:
            bundle.obj.save()
        return bundle
