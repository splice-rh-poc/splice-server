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
import django
import gzip
import logging
import time
import StringIO
import json

from bson import json_util
from datetime import datetime
from dateutil.tz import tzutc

from tastypie import http
from tastypie.authentication import MultiAuthentication
from tastypie.authorization import Authorization
from tastypie.exceptions import NotFound, BadRequest, InvalidFilterError, HydrationError, InvalidSortError, ImmediateHttpResponse, Unauthorized
from tastypie.resources import Resource
from tastypie_mongoengine.resources import MongoEngineResource
from tastypie.utils import dict_strip_unicode_keys


from splice.common import certs, config, utils
from splice.common.auth import X509CertificateAuthentication, TwoLeggedOAuthAuthentication, SpliceAuth
from splice.common.models import Pool, Product, Rules, SpliceServer, MarketingProductUsage, ProductUsage, get_now
from splice.common.deserializer import JsonGzipSerializer

_LOG = logging.getLogger(__name__)


class PingResource(Resource):
    # Simple API used to test if basic 'plumbing' is working
    # Returns a 'pong' message with current datetime
    class Meta:
        resource_name = 'ping'
        list_allowed_methods = ["get", "post", "put"]
        authentication = SpliceAuth()
        authorization = Authorization()

    def get_list(self, request, **kwargs):
        return self.pong()

    def put_list(self, request, **kwargs):
        return self.pong()

    def post_list(self, request, **kwargs):
        return self.pong()

    def pong(self):
        message = {"pong": str(datetime.now(tzutc()))}
        return http.HttpAccepted(utils.obj_to_json(message))


class BaseResource(MongoEngineResource):

    def __init__(self):
        super(BaseResource, self).__init__()
        self.all_objects = [] 

    class Meta:
        authorization = Authorization()
        authentication = X509CertificateAuthentication(verification_ca=certs.get_splice_server_identity_ca_pem())
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get']
        serializer = JsonGzipSerializer()

    def hydrate_created(self, bundle):
        if bundle.data.has_key("created"):
            value = utils.convert_to_datetime(bundle.data["created"])
            if not value:
                value = get_now()
            bundle.data["created"] = value
        return bundle

    def hydrate_updated(self, bundle):
        if bundle.data.has_key("updated"):
            value = utils.convert_to_datetime(bundle.data["updated"])
            if not value:
                value = get_now()
            bundle.data["updated"] = value
        return bundle

    def put_list(self, request, **kwargs):
        """
        Replaces a collection of resources with another collection.

        Calls ``delete_list`` to clear out the collection then ``obj_create``
        with the provided the data to create the new collection.

        Return ``HttpNoContent`` (204 No Content) if
        ``Meta.always_return_data = False`` (default).

        Return ``HttpAccepted`` (202 Accepted) if
        ``Meta.always_return_data = True``.
        """
        ## Overwriting what default tastypie does because
        ## We do _not_ want to delete all prior objects in collection, which is default behavior for tastypie
        if django.VERSION >= (1, 4):
            body = request.body
        else:
            body = request.raw_post_data
        deserialized = self.deserialize(request, body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        deserialized = self.alter_deserialized_list_data(request, deserialized)

        if not self._meta.collection_name in deserialized:
            raise BadRequest("Invalid data sent.")

        basic_bundle = self.build_bundle(request=request)
        ##
        ## This is the change we are doing from default tastypie, do not delete the collection details
        ##
        #self.obj_delete_list_for_update(bundle=basic_bundle, **self.remove_api_resource_names(kwargs))
        ##
        bundles_seen = []

        for object_data in deserialized[self._meta.collection_name]:
            bundle = self.build_bundle(data=dict_strip_unicode_keys(object_data), request=request)

            # Attempt to be transactional, deleting any previously created
            # objects if validation fails.
            try:
                self.obj_create(bundle=bundle, **self.remove_api_resource_names(kwargs))
                bundles_seen.append(bundle)
            except ImmediateHttpResponse:
                self.rollback(bundles_seen)
                raise

        if not self._meta.always_return_data:
            return http.HttpNoContent()
        else:
            to_be_serialized = {}
            to_be_serialized[self._meta.collection_name] = [self.full_dehydrate(bundle, for_list=True) for bundle in bundles_seen]
            to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)
            return self.create_response(request, to_be_serialized, response_class=http.HttpAccepted)


    def post_list(self, request, **kwargs):
        # Changing behavior so post to a list will update the collection opposed to
        # only working on a single item.
        # Note:  tastypie uses 'put_list' to update a collection
        #                      'post_list' to update a single element of a collection
        #
        # Further...'put_list' defaults to deleting the existing items in a collection before adding the new items
        
        self.all_objects = []   # We need to reset 'all_objects' on each request, this is intended
                                # to save the objects from this request which are created with obj_create
                                # we want to invoke self.complete_hook() with all objects in request
        _LOG.debug("request data: " + request.raw_post_data)
        self.put_list(request, **kwargs)
        self.complete_hook(self.all_objects)

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
        self.is_valid(bundle)
        if bundle.errors:
            self.error_response(bundle.errors, request)
        obj = self.create_hook(bundle.obj)
        self.all_objects.append(obj)
        return bundle

    def create_hook(self, obj):
        """
        Called to save a single object after it's been deserialized.
        This method is responsible for determining if this object is new/updated and should
        be saved to database, or is it an older version and should be ignored.

        @param obj: serialized object
        @return: the object 'obj' or a modified version of it needs to be returned
        """
        existing = self.get_existing(obj)
        if not existing:
            obj.save()
        else:
            _LOG.info("Existing = '%s'" % (existing))
            if obj.updated > existing.updated:
                for key, value in obj._data.items():
                    if key and key != "id":
                        # Skip the 'None' which is part of the data sent if the obj has not been saved previously
                        _LOG.info("Updating '%s'='%s'" % (key, value))
                        setattr(existing, key, value)
                existing.save()
            else:
                _LOG.debug("Ignoring %s since it is not newer than what is in DB" % (obj))
        return obj

    def complete_hook(self, objects):
        """
        Called after all items have been serialized and create_hook has fired for each item.
        Used primarily by ReportServer to process "import" of items, where the items sent in this
        request are not saved directly to DB...instead they are batch processed and transformed 
        into ReportData.

        @param objects: list of all serialized objects from this request
        @return None
        """
        pass

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
        return MarketingProductUsage.objects(instance_identifier=obj.instance_identifier, checkin_date=obj.checkin_date).first()


class RulesResource(BaseResource):
    class Meta(BaseResource.Meta):
        queryset = Rules.objects.all()

    def get_existing(self, obj):
        return Rules.objects(version=obj.version).first()

    def create_hook(self, obj):
        existing = self.get_existing(obj)
        if not existing:
            obj.save()
            return

        _LOG.info("existing = '%s'" % (existing))
        if obj.version > existing.version:
            for key, value in obj._data.items():
                if key and key != "id":
                    setattr(existing, key, value)
            existing.save()
        else:
            _LOG.debug("Ignoring version %s of Rules since it is not newer than what is in DB: version %s" % \
                       (obj.version, existing.version))


class SpliceServerResource(BaseResource):
    class Meta(BaseResource.Meta):
        queryset = SpliceServer.objects.all()

    def get_existing(self, obj):
        return SpliceServer.objects(uuid=obj.uuid).first()


###
# TODO:  Consider refactoring ProductUsageResource to inherit from BaseResource
#        this will change the usage of the API, therefore clients will need to make changes
#
#         Background:  ProductUsageResource was one of the first REST APIs we wrote, originally resided in ReportServer
#                      now exists in splice.common.api so we can keep all common APIs together
###
class ProductUsageResource(MongoEngineResource):

    class Meta:
        queryset = ProductUsage.objects.all()
        authorization = Authorization()


    def post_list(self, request, **kwargs):
        if not request.raw_post_data:
            _LOG.info("Empty body in request")
            return http.HttpBadRequest("Empty body in request")
        try:
            raw_post_data = request.raw_post_data
            _LOG.info("ProductUsageResource::post_list() processing %s KB." % (len(request.raw_post_data)/1024.0))
            if request.META.has_key("HTTP_CONTENT_ENCODING") and request.META["HTTP_CONTENT_ENCODING"] == "gzip":
                start_unzip = time.time()
                data = StringIO.StringIO(raw_post_data)
                gzipper = gzip.GzipFile(fileobj=data)
                raw_post_data = gzipper.read()
                end_unzip = time.time()
                _LOG.info("ProductUsageResource::post_list() uncompressed %s KB to %s KB in %s seconds" % \
                          (len(request.raw_post_data)/float(1024),
                           len(raw_post_data)/float(1024), end_unzip - start_unzip))
            a = time.time()
            product_usage = json.loads(raw_post_data, object_hook=json_util.object_hook)
            if isinstance(product_usage, dict):
                product_usage = [product_usage]
            pu_models = [ProductUsage._from_son(p) for p in product_usage]
            for pu in pu_models:
                if isinstance(pu.date, basestring):
                    # We must convert from str to datetime for ReportServer to be able to process this data
                    pu.date = utils.convert_to_datetime(pu.date)
            b = time.time()
            items_not_imported = self.import_hook(pu_models)
            c = time.time()
            _LOG.info("ProductUsageResource::post_list() Total Time: %s,  %s seconds to convert %s KB to JSON. "
                  "%s seconds to import %s objects into mongo with %s errors." % (c-a, b-a,
                        len(raw_post_data)/1024.0, c-b, len(pu_models), items_not_imported))
            if not items_not_imported:
                return http.HttpAccepted()
            else:
                return http.HttpConflict(items_not_imported)
        except Exception, e:
            _LOG.exception("Unable to process request with %s bytes in body" % (len(raw_post_data)))
            _LOG.info("Snippet of failed request body: \n%s\n" % (raw_post_data[:8*1024]))
            return http.HttpBadRequest(e)

# import hook is overriden in sreport.api
    def import_hook(self, product_usage):
        """
        @param product_usage:
        @return: a list of items which failed to import.
        """
        raise NotImplementedError
