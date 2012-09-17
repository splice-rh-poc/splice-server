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
        "get_all_rhics_url": CONFIG.get("rhic_serve", "get_all_rhics_url")
    }

def get_logging_config_file():
    return CONFIG.get("logging", "config")