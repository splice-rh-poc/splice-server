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
import logging
import logging.config
import os
import sys

from django.conf import settings

from splice.common.exceptions import BadConfigurationException

CONFIG = None

# TODO:  Add logic to validate configuration entries and log/throw exception
# early to warn user of issues

defaults = {
    'server': {
        'db_name': 'checkin_service',
        'db_host': 'localhost',
    },
}

def init(config_file=None, reinit=False):
    global CONFIG
    if CONFIG and not reinit:
        return CONFIG
    if not config_file:
        config_file = settings.SPLICE_CONFIG_FILE
    CONFIG = ConfigParser.SafeConfigParser()
    CONFIG.read(config_file)
    read_config_files()
    init_logging()
    return CONFIG


def read_config_files():
    global CONFIG
    if CONFIG.has_option('main', 'config_dir'):
        config_dir = CONFIG.get('main', 'config_dir')
        for config_file in os.listdir(config_dir):
            if not config_file.endswith('.conf'):
                continue
            else:
                CONFIG.read(os.path.join(config_dir, config_file))


def reset_logging():
    # Not super elegant, but this is the easiest way to reset the python
    # logging module.
    logging.Logger.manager.loggerDict = {}


def init_logging():
    reset_logging()
    splice_log_cfg = get_logging_config_file()
    if splice_log_cfg:
        if not os.path.exists(splice_log_cfg):
            print "Unable to read '%s' for logging configuration" % (splice_log_cfg)
        else:
            try:
                logging.config.fileConfig(splice_log_cfg)
            except Exception, e:
                print e
                print "Unable to initialize logging config with: %s" % (splice_log_cfg)


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

    try:
        rhic_serve_config = {
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
    except Exception:
        rhic_serve_config = {}

    return rhic_serve_config

def get_reporting_config_info(cfg=None):
    if not cfg:
        cfg = CONFIG
    try:
        raw_servers = cfg.get("reporting", "servers")
    except Exception, e:
        servers = raw_servers = None

    if raw_servers:
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
    try:
        upload_interval = cfg.getint("tasks", "upload_product_usage_interval_minutes")
    except:
        upload_interval = 240

    try:
        limit_per_call = cfg.getint("tasks", "upload_product_usage_limit_per_call")
    except:
        limit_per_call = 10000

    return {
        "servers": servers,
        "upload_interval_minutes": upload_interval,
        "limit_per_call": limit_per_call
    }

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
    if CONFIG.has_option('logging', 'config'):
        return CONFIG.get("logging", "config")
    else:
        return None
