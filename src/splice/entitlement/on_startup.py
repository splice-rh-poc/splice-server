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

####
# Placeholder for functionality we want to run on startup
#
# We are checking & logging errors with config parsing here instead of the 'config' module
# to avoid cyclic dependency issues, since we want to use logging, and logging is setup from
# config files read from the 'config'.  Our plan is to allow config & logging to initialize
# and only after they are initialized do we check config values and warn of issues
###


from datetime import timedelta
import logging
import os

from django.conf import settings

from splice.common import config
from certutils.certutils import CertFileUtils

_LOG = logging.getLogger(__name__)

def run():

    config.init()
    configure_logging()
    configure_celery()

    if not check_certs():
        _LOG.warning("Please re-check the configuration file, there appears to be problems with how certificates have been configured")

    if not check_valid_identity(cert=config.get_splice_server_identity_cert_path(),
        key=config.get_splice_server_identity_key_path(),
        ca_cert=config.get_splice_server_identity_ca_path()):
        _LOG.error("*****\n"
                    "Invalid configuration for Splice Server Identity Certificate/Key/CA.\n"
                    "Certificate information failed validation check.\n"
                    "Please re-check configuration and restart Splice.  Web Services will be inactive until this is resolved.\n"
                    "*****")
    _LOG.info("Configuration file was examined and certificate configuration is acceptable.")


def configure_logging():
    splice_log_cfg = config.get_logging_config_file()
    if splice_log_cfg:
        if not os.path.exists(splice_log_cfg):
            print "Unable to read '%s' for logging configuration" % (splice_log_cfg)
        else:
            try:
                logging.config.fileConfig(splice_log_cfg)
            except Exception, e:
                print e
                print "Unable to initialize logging config with: %s" % (splice_log_cfg)


def configure_celery():

    CELERYBEAT_SCHEDULE = {}

    rhic_serve_cfg = config.get_rhic_serve_config_info()

    single_rhic_retry_lookup_tasks_in_minutes = 15
    if rhic_serve_cfg.has_key("single_rhic_retry_lookup_tasks_in_minutes"):
        single_rhic_retry_lookup_tasks_in_minutes = rhic_serve_cfg["single_rhic_retry_lookup_tasks_in_minutes"]

    CELERYBEAT_SCHEDULE = {
        # Executes every 30 seconds
        #'dummy_task_executes_every_hour': {
        #    'task': '%s.log_time' % (SPLICE_ENTITLEMENT_BASE_TASK_NAME),
        #    'schedule': timedelta(seconds=5),
        #    'args': None,
        #},
        'process_running_rhic_lookup_tasks': {
            'task': '%s.process_running_rhic_lookup_tasks' % (settings.SPLICE_ENTITLEMENT_BASE_TASK_NAME),
            'schedule': timedelta(minutes=single_rhic_retry_lookup_tasks_in_minutes),
           'args': None,
        }
    }

    # Controls 'if' we will sync all rhics
    sync_all_rhics_bool = True
    if rhic_serve_cfg.has_key("sync_all_rhics_bool"):
        sync_all_rhics_bool = rhic_serve_cfg["sync_all_rhics_bool"]
    if sync_all_rhics_bool:
        # Controls 'when' we will run a full sync of rhics
        sync_all_rhics_in_minutes = 60
        if rhic_serve_cfg.has_key("sync_all_rhics_in_minutes"):
            sync_all_rhics_in_minutes = int(rhic_serve_cfg["sync_all_rhics_in_minutes"])
        CELERYBEAT_SCHEDULE['sync_all_rhics'] = {
            'task': '%s.sync_all_rhics' % (settings.SPLICE_ENTITLEMENT_BASE_TASK_NAME),
            'schedule': timedelta(minutes=sync_all_rhics_in_minutes),
            'args': None,
        }

    report_info = config.get_reporting_config_info()
    if report_info["servers"]:
        CELERYBEAT_SCHEDULE['upload_product_usage'] = {
            'task': '%s.upload_product_usage' % (settings.SPLICE_ENTITLEMENT_BASE_TASK_NAME),
            'schedule': timedelta(minutes=report_info["upload_interval_minutes"]),
            'args': None,
        }
    else:
        _LOG.warning("Skipped configuring a periodic task to upload Product Usage since no servers were configured.")

    _LOG.debug("CeleryBeat configuration: %s" % (CELERYBEAT_SCHEDULE))

    settings.CELERYBEAT_SCHEDULE = CELERYBEAT_SCHEDULE

def check_valid_identity(cert, key, ca_cert):
    # Check that the identity certificate was signed by the configured identity CA
    certfu = CertFileUtils()
    if not certfu.validate_certificate(config.get_splice_server_identity_cert_path(),
        config.get_splice_server_identity_ca_path()):
        _LOG.error("[security].splice_server_identity_cert failed validation against CA: [security].splice_server_identity_ca")
        return False
    if not certfu.validate_priv_key_to_certificate(key, cert):
        _LOG.error("[security].splice_server_identity_key is not matched to [security].splice_server_identity_cert")
        return False
    return True

def check_certs():
    status = _check_path(config.get_splice_server_identity_cert_path(), "[security].splice_server_identity_cert")
    status &= _check_path(config.get_splice_server_identity_ca_path(), "[security].splice_server_identity_ca")
    status &= _check_path(config.get_splice_server_identity_key_path(), "[security].splice_server_identity_key")
    status &= _check_path(config.get_rhic_ca_path(), "[security].rhic_ca_path")
    rhic_serve_cfg = config.get_rhic_serve_config_info()
    status &= _check_path(rhic_serve_cfg["client_key"], "[rhic_serve].client_key")
    status &= _check_path(rhic_serve_cfg["client_cert"], "[rhic_serve].client_cert")
    return status

def _check_path(path, identifier):
    if not path:
        _LOG.warning("%s is not set")
        return False
    if not os.path.exists(path):
        _LOG.error("%s: path '%s' does not exist" % (identifier, path))
        return False
    f = open(path)
    try:
        buff = f.read()
    except Exception, e:
        _LOG.exception("%s: unable to read '%s'" % (identifier, path))
        return False
    finally:
        f.close()
    return True

