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

CONFIG = None

def init(config_file=None):
    global CONFIG
    if CONFIG:
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
    return {
        "host": CONFIG.get("rhic_serve", "host"),
        "port": CONFIG.get("rhic_serve", "port"),
        "get_all_rhics_url": CONFIG.get("rhic_serve", "get_all_rhics_url"),
        "task_schedule_minutes": CONFIG.get("rhic_serve", "task_schedule_minutes"),
    }

def get_logging_config_file():
    return CONFIG.get("logging", "config")

def get_splice_server_info():
    ret_val = {}
    ret_val["description"] = CONFIG.get("info", "description")
    ret_val["environment"] = CONFIG.get("info", "environment")
    ret_val["uuid"] = CONFIG.get("info", "uuid")
    ret_val["hostname"] = CONFIG.get("info", "hostname")
    return ret_val