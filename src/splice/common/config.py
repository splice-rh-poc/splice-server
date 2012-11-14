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


CONFIG = None

# TODO:  Add logic to validate configuration entries and log/throw exception
# early to warn user of issues

class BadConfigurationException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "Server configuration error: %s" % self.msg


defaults = \
{
    'crl': {
        'location': '/etc/pki/splice',
    },
    'entitlement': {
        'host': 'ec2-107-20-23-80.compute-1.amazonaws.com',
        'password': 'admin',
        'port': '8080',
        'url': '/splice',
        'username': 'admin',
    },
    'info': {
        'description': '"TBD"',
        'environment': '"us-east-1"',
        'hostname': '"test_splice_server.example.com"',
    },
    'logging': {
        'config': '/etc/splice/logging/basic.cfg',
    },
    'main': {
        'config_dir': '/etc/splice/conf.d',
    },
    'reporting': {
    },
    'rhic_serve': {
        'client_cert': '/etc/pki/splice/generated/Splice_identity.cert',
        'client_key': '/etc/pki/splice/generated/Splice_identity.key',
        'host': 'ec2-54-242-25-138.compute-1.amazonaws.com',
        'port': '443',
        'rhics_url': '/api/v1/rhicrcs/',
        'db_name': 'rhic_serve',
        'db_host': 'localhost',
    },
    'security': {
        'rhic_ca_cert': '/etc/pki/splice/Splice_testing_root_CA.crt',
        'rhic_ca_key': '/etc/pki/splice/Splice_testing_root_CA.key',
        'rhic_ca_srl': '/etc/pki/splice/Splice_testing_root_CA.srl',
        'sign_days': '1000',
        'splice_server_identity_ca': '/etc/pki/splice/Splice_testing_root_CA.crt',
        'splice_server_identity_cert': '/etc/pki/splice/generated/Splice_identity.cert',
        'splice_server_identity_key': '/etc/pki/splice/generated/Splice_identity.key',
    },
    'server': {
        'db_host': 'localhost',
        'db_name': 'checkin_service',
    },
    'tasks': {
        'single_rhic_lookup_cache_unknown_in_hours': '24',
        'single_rhic_lookup_timeout_in_minutes': '30',
        'single_rhic_retry_lookup_tasks_in_minutes': '2',
        'sync_all_rhics_bool': 'true',
        'sync_all_rhics_in_minutes': '60',
        'sync_all_rhics_pagination_limit_per_call': '25000',
        'upload_product_usage_interval_minutes': '240',
        'upload_product_usage_limit_per_call': '10000',
    },
}


def init(config_file=None, reinit=False):
    global CONFIG
    if CONFIG and not reinit:
        return CONFIG
    CONFIG = ConfigParser.SafeConfigParser()
    set_defaults()
    CONFIG.read(config_file)
    read_config_files()
    init_logging()
    return CONFIG


def set_defaults():
    global CONFIG
    for section, configs in defaults.items():
        if not CONFIG.has_section(section):
            CONFIG.add_section(section)
        for config, value in configs.items():
            CONFIG.set(section, config, value)


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
    rhic_serve_config = {
        "host": CONFIG.get("rhic_serve", "host"),
        "port": CONFIG.get("rhic_serve", "port"),
        "rhics_url": CONFIG.get("rhic_serve", "rhics_url"),
        "sync_all_rhics_in_minutes": 
            CONFIG.getint("tasks", "sync_all_rhics_in_minutes"),
        "single_rhic_lookup_cache_unknown_in_hours": 
            CONFIG.getint("tasks", "single_rhic_lookup_cache_unknown_in_hours"),
        "single_rhic_lookup_timeout_in_minutes": 
            CONFIG.getint("tasks", "single_rhic_lookup_timeout_in_minutes"),
        "single_rhic_retry_lookup_tasks_in_minutes": 
            CONFIG.getint("tasks", "single_rhic_retry_lookup_tasks_in_minutes"),
        "sync_all_rhics_bool" : 
            CONFIG.getboolean("tasks", "sync_all_rhics_bool"),
        "sync_all_rhics_pagination_limit_per_call" : 
            CONFIG.getint("tasks", "sync_all_rhics_pagination_limit_per_call"),
        "client_cert": CONFIG.get("rhic_serve", "client_cert"),
        "client_key": CONFIG.get("rhic_serve", "client_key"),
    }

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
                raise BadConfigurationException(
                    "unable to parse '%s' for reporting server info, "
                    "expected in format of address:port:url" % (s))
            addr = pieces[0].strip()
            try:
                port = int(pieces[1].strip())
            except:
                raise BadConfigurationException(
                    "unable to convert '%s' to an integer port for server "
                    "info line of '%s'" % (pieces[1], s))
            url = pieces[2].strip()
            servers.append((addr, port, url))

    upload_interval = cfg.getint("tasks", 
                                 "upload_product_usage_interval_minutes")
    limit_per_call = cfg.getint("tasks", 
                                "upload_product_usage_limit_per_call")

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
    return CONFIG.get("logging", "config")
