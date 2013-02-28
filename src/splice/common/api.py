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
from splice.common.models import Pool, Product, Rules, SpliceServer, MarketingProductUsage

_LOG = logging.getLogger(__name__)


class BaseResource(MongoEngineResource):

    class Meta:
        authorization = Authorization()
        authentication = X509CertificateAuthentication(verification_ca=certs.get_splice_server_identity_ca_pem())
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get']

    def hydrate_created(self, bundle):
        bundle.data["created"] = utils.convert_to_datetime(bundle.data["created"])
        return bundle

    def hydrate_updated(self, bundle):
        bundle.data["updated"] = utils.convert_to_datetime(bundle.data["updated"])
        return bundle

    def post_list(self, request, **kwargs):
        # Changing behavior so post to a list will update the collection opposed to
        # only working on a single item.
        # Note:  tastypie uses 'put_list' to update a collection
        #                      'post_list' to update a single element of a collection
        #
        # Further...'put_list' defaults to deleting the existing items in a collection before adding the new items
        super(BaseResource, self).put_list(request, **kwargs)

    def obj_delete_list(self, request=None, **kwargs):
        # We are intentionally changing the tastypie default behavior of
        # deleting the entire collection on each collection 'PUT'
        pass

    def obj_create(self, bundle, request=None, **kwargs):
        bundle.obj = self._meta.object_class()
        _LOG.info("obj_create invoked for %s with bundle: %s" % (bundle.obj.__class__, bundle))
        for key, value in kwargs.items():
            setattr(bundle.obj, key, value)
        bundle = self.full_hydrate(bundle)
        self.is_valid(bundle, request)
        if bundle.errors:
            self.error_response(bundle.errors, request)
        self.update_if_newer(bundle)
        return bundle

    def update_if_newer(self, bundle):
        existing = self.get_existing(bundle.obj)
        if not existing:
            bundle.obj.save()
            return

        _LOG.info("existing = '%s'" % (existing))
        if bundle.obj.updated > existing.updated:
            for key, value in bundle.obj._data.items():
                if key and key != "id":
                    # Skip the 'None' which is part of the data sent if the obj has not been saved previously
                    _LOG.info("Updating '%s'='%s'" % (key, value))
                    setattr(existing, key, value)
            existing.save()
        else:
            _LOG.debug("Ignoring %s since it is not newer than what is in DB" % (bundle.obj))

    ##
    ## Below needs to be implemented by those who inherit
    ##
    def get_existing(self, obj):
        raise NotImplementedError()


class PoolResource(BaseResource):
    class Meta(BaseResource.Meta):
        queryset = Pool.objects.all()

    def get_existing(self, obj):
        return Pool.objects(uuid=obj.uuid).first()

    def hydrate_active(self, bundle):
        bundle.data["active"] = utils.str2bool(bundle.data["active"])
        return bundle


class ProductResource(BaseResource):
    class Meta(BaseResource.Meta):
        queryset = Product.objects.all()

    def get_existing(self, obj):
        return Product.objects(product_id=obj.product_id).first()

class MarketingProductUsageResource(BaseResource):
    class Meta(BaseResource.Meta):
        queryset = MarketingProductUsage.objects.all()

    def get_existing(self, obj):
        return MarketingProductUsage.objects(instance_identifier=obj.instance_identifier, date=obj.date).first()

class RulesResource(BaseResource):
    class Meta(BaseResource.Meta):
        queryset = Rules.objects.all()

    def get_existing(self, obj):
        return Rules.objects(version=obj.version).first()

    def update_if_newer(self, bundle):
        existing = self.get_existing(bundle.obj)
        if not existing:
            bundle.obj.save()
            return

        _LOG.info("existing = '%s'" % (existing))
        if bundle.obj.version > existing.version:
            for key, value in bundle.obj._data.items():
                if key and key != "id":
                    setattr(existing, key, value)
            existing.save()
        else:
            _LOG.debug("Ignoring version %s of Rules since it is not newer than what is in DB: version %s" % \
                       (bundle.obj.version, existing.version))


class SpliceServerResource(BaseResource):
    class Meta(BaseResource.Meta):
        queryset = SpliceServer.objects.all()

    def get_existing(self, obj):
        return SpliceServer.objects(uuid=obj.uuid).first()


