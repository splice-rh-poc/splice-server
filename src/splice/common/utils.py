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

from logging import getLogger

from splice.common.exceptions import UnsupportedDateFormatException

from datetime import datetime
from dateutil.tz import tzutc
import isodate
import json


_LOG = getLogger(__name__)


class MongoEncoder(json.JSONEncoder):
    def default(self, obj, **kwargs):
        from pymongo.objectid import ObjectId
        import mongoengine
        import types
        if isinstance(obj, (mongoengine.Document, mongoengine.EmbeddedDocument)):
            out = dict(obj._data)
            if out.has_key(None):
                # Remove the "null":null entry caused with a MongoEngine ObjectId has not been
                # saved or initialized
                del out[None]
            for k,v in out.items():
                if isinstance(v, ObjectId):
                    out[k] = str(v)
            return out
        elif isinstance(obj, mongoengine.queryset.QuerySet):
            return list(obj)
        elif isinstance(obj, types.ModuleType):
            return None
        elif isinstance(obj, (list,dict)):
            return obj
        elif isinstance(obj, datetime):
            return str(obj)
        else:
            return json.JSONEncoder.default(obj, **kwargs)

def obj_to_json(obj, indent=None):
    """
    Converts a mongoengine object to json
    @param obj:
    @return:
    """
    return json.dumps(obj, cls=MongoEncoder, indent=indent)

def sanitize_key_for_mongo(input):
    def _sanitize(input_str):
        return input.replace(".", "_dot_").replace("$", "_dollarsign_")

    if isinstance(input, list):
        ret_val = []
        for key in input:
            ret_val.append(sanitize_key_for_mongo(key))
        return ret_val
    return _sanitize(input)


def sanitize_dict_for_mongo(input_dict):
    """
    @param input_dict   dictionary to be processed and convert all "." and "$" to safe characters
                        "." are translated to "_dot_"
                        "$" are translated to "_dollarsign_"
    @type input_dict: dict

    @return safe dictionary able to store in mongo
    @rtype: dict
    """
    ret_val = {}
    for key in input_dict:
        cleaned_key = sanitize_key_for_mongo(key)
        ret_val[cleaned_key] = input_dict[key]
    return ret_val

def convert_to_datetime(input_date_str):
    """
    Converts a string representation of an isodate into a datetime instance.
    Handles the situation of the seconds containing decimal values
    Below are all valid string representation this function will convert:
     '2012-09-19T19:01:55.008000+00:00'
     '2012-09-19T19:01:55+00.00'
     '2012-09-19T19:01:55'
    @param input_date_str:
    @return:
    @rtype: datetime.datetime
    """
    def ensure_tzinfo(input):
        if not input.tzinfo:
            return input.replace(tzinfo=tzutc())
        return input

    if input_date_str is None:
        return None
    try:
        return ensure_tzinfo(isodate.parse_datetime(input_date_str))
    except Exception, e:
        try:
            # Fallback to a non iso format datetime parser
            from dateutil.parser import parser
            return ensure_tzinfo(parser().parse(input_date_str))
        except:
            pass
        _LOG.exception("Unable to parse date: %s" % (input_date_str))
        raise UnsupportedDateFormatException(input_date_str)


def str2bool(v):
    if isinstance(v, basestring):
        return v.lower() in ("yes", "true", "t", "1")
    return v