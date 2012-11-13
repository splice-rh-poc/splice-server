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

class SpliceServer(Document):
    uuid = StringField(required=True, unique=True)
    description = StringField() # Example what datacenter is this deployed to, i.e. us-east-1
    hostname = StringField(required=True)
    environment = StringField(required=True)
   
    meta = {'allow_inheritance': True}

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

class ProductUsageTransferInfo(Document):
    server_hostname = StringField(required=True, unique=True)
    last_timestamp = IsoDateTimeField(required=True)

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        """
        pre_save signal hook.
        """
        # Ensure that the 'server_hostname' has any "." removed so it can be a key in mongo
        document.server_hostname = sanitize_key_for_mongo(document.server_hostname)

    def __str__(self):
        return "ProductUsageTransferInfo, server_hostname = %s, last_timestamp = %s" % (self.server_hostname, self.last_timestamp)

class ConsumerIdentity(RHIC):

    def __str__(self):
        msg = "Consumer Identity '%s' with engineering_ids '%s', " \
              "created_date '%s', modified_date '%s'" %\
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
    facts = DictField()

    meta = {'allow_inheritance': True}

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if isinstance(document.date, basestring):
            document.date = convert_to_datetime(document.date)
        if document.facts:
            document.facts = sanitize_dict_for_mongo(document.facts)

    def __str__(self):
        return "Consumer '%s' on Splice Server '%s' from instance '%s' "" \
            ""with allowed_products '%s', "" \
            ""unallowed_products %s at '%s'" % \
            (self.consumer, self.splice_server,
            self.instance_identifier, self.allowed_product_info,
            self.unallowed_product_info,
            self.date)


# Signals
signals.pre_save.connect(IdentitySyncInfo.pre_save, sender=IdentitySyncInfo)
signals.pre_save.connect(ProductUsage.pre_save, sender=ProductUsage)
