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

from datetime import datetime
from dateutil.tz import tzutc

from mongoengine import DateTimeField, Document, ListField, StringField, DictField, IntField, BooleanField
from mongoengine import signals
from rhic_serve.common.fields import IsoDateTimeField
from rhic_serve.rhic_rcs.models import RHIC
from splice.common.utils import sanitize_key_for_mongo, sanitize_dict_for_mongo, convert_to_datetime


def get_now():
    return datetime.now(tzutc())


class Pool(Document):
    uuid = StringField(unique=True, required=True)
    account = IntField(required=True)
    active = BooleanField(default=True)
    contract = IntField()
    product_id = StringField(required=True)
    product_name = StringField(required=True)
    # product_attributes may vary common keys are:
    #  "option_code", "enabled_consumer_types", "variant"
    #  "name", "type", "support_level", "description", "support_type",
    #  "product_family", "sockets", "virt_limit", "subtype"
    product_attributes = DictField()
    provided_products = ListField(DictField())  # [ {"id":value, "name":value} ]
    created = IsoDateTimeField(required=True)
    start_date = IsoDateTimeField(required=True)
    end_date = IsoDateTimeField(required=True)
    updated = IsoDateTimeField(required=True)
    quantity = IntField(required=True)
    
    meta = {
        'allow_inheritance': True,
    }

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        for attr_name in ["created", "start_date", "end_date", "updated"]:
            if isinstance(getattr(document, attr_name), basestring):
                setattr(document, attr_name,
                        convert_to_datetime(getattr(document, attr_name)))
        if document.product_attributes:
            document.product_attributes = \
                sanitize_dict_for_mongo(document.product_attributes)

    def __str__(self):
        return "Pool<%s, %s> account=<%s>, contract=<%s>, active=%s, quantity=<%s>, created=<%s>, " \
            "updated=<%s>, start_date=<%s>, end_date=<%s> provided_products=<%s>," \
            "product_attributes=<%s>" % \
            (self.product_id, self.product_name, self.account, self.contract, self.active, self.quantity,
             self.created, self.updated, self.start_date, self.end_date, self.provided_products,
             self.product_attributes)

    def update_to(self, other):
        self.account = other.account
        self.active = other.active
        self.contract = other.contract
        self.product_id = other.product_id
        self.product_name = other.product_name
        self.product_attributes = other.product_attributes
        self.provided_products = other.provided_products
        self.created = other.created
        self.start_date = other.start_date
        self.end_date = other.end_date
        self.updated = other.updated
        self.quantity = other.quantity


class Product(Document):
    product_id = StringField(required=True, unique=True)
    name = StringField(required=True)
    engineering_ids = ListField()
    created = IsoDateTimeField(required=True)
    updated = IsoDateTimeField(required=True)
    eng_prods = ListField(DictField())  # Information on Engineering Products [{"id", "label", "name", "vendor"}]
    attrs = DictField()  # Product Attributes
    dependent_product_ids = ListField()

    meta = {
        'allow_inheritance': True,
    }

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        for attr_name in ["created", "updated"]:
            if isinstance(getattr(document, attr_name), basestring):
                setattr(document, attr_name,
                        convert_to_datetime(getattr(document, attr_name)))
        if document.attrs:
            document.attrs = sanitize_dict_for_mongo(document.attrs)

    def __str__(self):
        return "Product<%s, %s>, engineering_ids=<%s>, attributes=<%s>,  created on %s, updated %s" % \
               (self.product_id, self.name, self.engineering_ids, self.attrs, self.created, self.updated)

    def update_to(self, other):
        self.product_id = other.product_id
        self.name = other.name
        self.engineering_ids = other.engineering_ids
        self.created = other.created
        self.updated = other.updated
        self.eng_prods = other.eng_prods
        self.attrs = other.attrs
        self.dependent_product_ids = other.dependent_product_ids


class Rules(Document):
    version = StringField(required=True, unique=True)
    data = StringField(required=True)

    meta = {
        'allow_inheritance': True,
    }

    def __str__(self):
        data_len = 0
        if self.data:
            data_len = len(self.data)
        return "Rules version=<%s> rules data is %s bytes" % (self.version, data_len)


class Contract(Document):
    # Unique Contract identifier
    contract_id = StringField(unique=True, required=True)
    # List of products associated with this contract
    products = ListField(StringField)  # Product Names

    meta = {
        'allow_inheritance': True,
    }


class SpliceServer(Document):
    uuid = StringField(required=True, unique=True)
    description = StringField() # Example what datacenter is this deployed to, i.e. us-east-1
    hostname = StringField(required=True)
    environment = StringField(required=True)
    created = IsoDateTimeField(required=True, default=get_now)
    updated = IsoDateTimeField(required=True, default=get_now)

    meta = {'allow_inheritance': True}

    def __str__(self):
        return "SpliceServer<%s>, hostname=<%s>, environment=<%s>, created on %s, last updated %s" % \
               (self.uuid, self.hostname, self.environment, self.created, self.updated)

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if isinstance(document.created, basestring):
            document.created = convert_to_datetime(document.created)
        if isinstance(document.updated, basestring):
            document.updated = convert_to_datetime(document.updated)


class RHICLookupTask(Document):
    meta = {
        'collection': 'rhic_lookup_task',
    }
    uuid = StringField(required=True, unique=True)
    task_id = StringField()
    initiated = IsoDateTimeField(required=True, default=get_now)
    modified = IsoDateTimeField(required=True, default=get_now)
    completed = BooleanField(default=False)
    status_code = IntField()

    def __str__(self):
        return "RHICLookupTask for '%s' initiated @ '%s', modified @ '%s', " \
               "completed = '%s', status_code = '%s', task_id = '%s'" % \
        (self.uuid, self.initiated, self.modified, self.completed, self.status_code, self.task_id)


class IdentitySyncInfo(Document):
    server_hostname = StringField(required=True, unique=True)
    last_sync = IsoDateTimeField(required=True)

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        """
        pre_save signal hook.
        """
        # Ensure that the 'server_hostname' has any "." removed so it can be a key in mongo
        document.server_hostname = sanitize_key_for_mongo(document.server_hostname)
    def __str__(self):
        return "IdentitySyncInfo, server_hostname = %s, last_sync = %s" % (self.server_hostname, self.last_sync)


class SpliceServerTransferInfo(Document):
    server_hostname = StringField(required=True, unique=True)
    last_timestamp = IsoDateTimeField(required=True)

    def __str__(self):
        return "%s, server_hostname = %s, last_timestamp = %s" % (self.__class__, self.server_hostname, self.last_timestamp)


class ConsumerIdentity(RHIC):
    meta = {
        'allow_inheritance': True,
    }

    def __str__(self):
        msg = "Consumer Identity '%s' with engineering_ids '%s', " \
              "created_date '%s', q_date '%s'" %\
              (self.uuid, self.engineering_ids, self.created_date,
                    self.modified_date)
        if self.deleted:
            msg += ", deleted = %s, deleted_date = %s" % (self.deleted, self.deleted_date)
        return msg

class ProductUsage(Document):
    consumer = StringField(required=True)
    splice_server = StringField(required=True) # uuid of Splice Server
    date = DateTimeField(required=True)
    instance_identifier = StringField(required=True, unique_with=['consumer', 'splice_server', 'date']) # example: MAC Address

    allowed_product_info = ListField(StringField())
    unallowed_product_info = ListField(StringField())
    tracker = ListField(StringField())

    facts = DictField()

    meta = {
        'allow_inheritance': True,
        'indexes': ['date', 'splice_server', 'consumer', 'instance_identifier', 'tracker'],
    }

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if isinstance(document.date, basestring):
            document.date = convert_to_datetime(document.date)
        if document.facts:
            document.facts = sanitize_dict_for_mongo(document.facts)
        # Ensure no duplicate entries are stored for document.tracker
        if document.tracker:
            document.tracker = list(set(document.tracker))

    def __str__(self):
        return "Consumer '%s' on Splice Server '%s' from instance '%s' "" \
            ""with allowed_products '%s', "" \
            ""unallowed_products %s at '%s'" % \
            (self.consumer, self.splice_server,
            self.instance_identifier, self.allowed_product_info,
            self.unallowed_product_info,
            self.date)


class MarketingProductUsage(Document):
    splice_server = StringField(required=True) # uuid of Splice Server data came from
    date = DateTimeField(required=True)
    instance_identifier = StringField(required=True, unique_with=['date'])
    updated = IsoDateTimeField(required=True, default=get_now)
    created = IsoDateTimeField(required=True, default=get_now)
    # XXX: a few of these may be required data
    entitlement_status = StringField()
    name = StringField()
    service_level = StringField()
    active = BooleanField()
    organization_id = StringField()
    organization_name = StringField()

    # product_info expected 'keys'
    # [{"account":value, "contract":value, "product":value, "quantity":value, 
    #   "sla":value, "support_level":value}]
    product_info = ListField(DictField())  

    facts = DictField()

    meta = {
        'allow_inheritance': True,
        'indexes': ['date', 'instance_identifier'],
        }

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if isinstance(document.date, basestring):
            document.date = convert_to_datetime(document.date)
        if document.facts:
            document.facts = sanitize_dict_for_mongo(document.facts)

    def __str__(self):
        return "MarketingProductUsage for <%s> on Splice Server <%s> at <%s> with instance identifier <%s>" % \
               (self.product_info, self.splice_server, self.date, self.instance_identifier)


class SingleTaskInfo(Document):
    #
    # SingleTaskInfo helps to enforce the behavior of a lock in mongodb
    # This lock behavior is used to restrict certain celery tasks to executing as only one at a time
    #
    task_id = StringField(required=True, unique=True)
    owner_pid = IntField(required=True)
    created = IsoDateTimeField(required=True, default=get_now)

    meta = {
        'indexes': ['task_id', 'owner_pid', ('task_id', 'owner_pid')],
    }
    def __str__(self):
        return "task_id '%s', owner_pid '%s', created on '%s'" % (self.task_id, self.owner_pid, self.created)

# Signals
signals.pre_save.connect(IdentitySyncInfo.pre_save, sender=IdentitySyncInfo)
signals.pre_save.connect(ProductUsage.pre_save, sender=ProductUsage)
signals.pre_save.connect(SpliceServer.pre_save, sender=SpliceServer)
signals.pre_save.connect(Pool.pre_save, sender=Pool)
signals.pre_save.connect(Product.pre_save, sender=Product)
signals.pre_save.connect(MarketingProductUsage.pre_save, sender=MarketingProductUsage)
