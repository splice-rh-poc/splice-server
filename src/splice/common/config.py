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

import ConfigParser
from splice.common import constants
from splice.common.exceptions import BadConfigurationException

CONFIG = None

#TODO:  Add logic to validate configuration entries and log/throw exception early to warn user of issues


def init(config_file=None, reinit=False):
    global CONFIG
    if CONFIG and not reinit:
        return CONFIG
    if not config_file:
        config_file = constants.SPLICE_CONFIG_FILE
    CONFIG = ConfigParser.SafeConfigParser()
    CONFIG.read(config_file)
    return CONFIG

def get_candlepin_config_info():

    return {
        "host": CONFIG.get("entitlement", "host"),
        "port": CONFIG.get("entitlement", "port"),
        "url": CONFIG.get("entitlement", "url"),
        "username": CONFIG.get("entitlement", "username"),
        "password": CONFIG.get("entitlement", "password"),
    }

def get_rhic_serve_config_info():
    client_cert = None
    client_key = None
    try:
        client_cert = CONFIG.get("rhic_serve", "client_cert")
    except Exception:
        pass
    try:
        client_key = CONFIG.get("rhic_serve", "client_key")
    except Exception:
        pass

    return {
        "host": CONFIG.get("rhic_serve", "host"),
        "port": CONFIG.get("rhic_serve", "port"),
        "rhics_url": CONFIG.get("rhic_serve", "rhics_url"),
        "sync_all_rhics_in_minutes": CONFIG.getint("tasks", "sync_all_rhics_in_minutes"),
        "single_rhic_lookup_cache_unknown_in_hours": CONFIG.getint("tasks", "single_rhic_lookup_cache_unknown_in_hours"),
        "single_rhic_lookup_timeout_in_minutes": CONFIG.getint("tasks", "single_rhic_lookup_timeout_in_minutes"),
        "single_rhic_retry_lookup_tasks_in_minutes": CONFIG.getint("tasks", "single_rhic_retry_lookup_tasks_in_minutes"),
        "sync_all_rhics_bool" : CONFIG.getboolean("tasks", "sync_all_rhics_bool"),
        "sync_all_rhics_pagination_limit_per_call" : CONFIG.getint("tasks", "sync_all_rhics_pagination_limit_per_call"),
        "client_cert": client_cert,
        "client_key": client_key,
    }

def get_reporting_config_info(cfg=None):
    if not cfg:
        cfg = CONFIG
    raw_servers = cfg.get("reporting", "servers")
    raw_servers = raw_servers.split(",")
    servers = []
    for s in raw_servers:
        pieces = s.split(":")
        if len(pieces) != 3:
            raise BadConfigurationException("unable to parse '%s' for reporting server info, expected in format of address:port:url" % (s))
        addr = pieces[0].strip()
        try:
            port = int(pieces[1].strip())
        except:
            raise BadConfigurationException("unable to convert '%s' to an integer port for server info line of '%s'" % (pieces[1], s))
        url = pieces[2].strip()
        servers.append((addr, port, url))
    return {"servers": servers}

def get_logging_config_file():
    return CONFIG.get("logging", "config")

def get_splice_server_info():
    ret_val = {}
    ret_val["description"] = CONFIG.get("info", "description")
    ret_val["environment"] = CONFIG.get("info", "environment")
    ret_val["hostname"] = CONFIG.get("info", "hostname")
    return ret_val

def get_rhic_ca_path():
    return CONFIG.get("security", "rhic_ca_cert")

def get_splice_server_identity_ca_path():
    return CONFIG.get("security", "splice_server_identity_ca")

def get_splice_server_identity_cert_path():
    return CONFIG.get("security", "splice_server_identity_cert")

def get_splice_server_identity_key_path():
    return CONFIG.get("security", "splice_server_identity_key")

def get_crl_path():
    return CONFIG.get("crl", "location")

def get_logging_config_file():
    return CONFIG.get("logging", "config")

