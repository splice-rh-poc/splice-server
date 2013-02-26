#!/usr/bin/env python
import json
import os
import sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "splice.checkin_service.settings")

from optparse import OptionParser
from splice.common import candlepin_client


def get_consumers(host, port, username, password, https):
    return candlepin_client.get_consumers(host, port, username, password, https)


def get_entitlements(host, port, username, password, https):
    return candlepin_client.get_entitlements(host, port, username, password, https)


def get_owners(host, port, username, password, https):
    return candlepin_client.get_owners(host, port, username, password, https)


def get_pools(host, port, username, password, https):
    return candlepin_client.get_pools(host, port, username, password, https)


def get_products(host, port, username, password, https):
    return candlepin_client.get_products(host, port, username, password, https)


def get_rules(host, port, username, password, https):
    return candlepin_client.get_rules(host, port, username, password, https)


def get_subscriptions(host, port, username, password, https):
    return candlepin_client.get_subscriptions(host, port, username, password, https)


def get_accounts():
    pass

if __name__ == "__main__":
    # Parse Args
    default_port=8443
    default_user="admin"
    default_password="admin"
    parser = OptionParser(description="Script to fetch data from a candlepin")
    parser.add_option('--host', action='store', default=None,
                      help="Hostname of Candlepin server")
    parser.add_option('--port', action='store', default=default_port,
                      help="Port of Candlepin server defaults to: %s" % (default_port))
    parser.add_option('--http', action='store_true', default=False, help="Use HTTP instead of HTTPs, default is False")
    parser.add_option('--user', action='store', default=default_user,
                      help="Username, default is %s" % default_user)
    parser.add_option('--password', action='store', default=default_password,
                      help="Password, default is %s" % default_password)
    (opts, args) = parser.parse_args()
    host = opts.host
    port = opts.port
    https = not opts.http
    username = opts.user
    password = opts.password

    if not host:
        print "Please re-run with --host"
        sys.exit(1)

    retval = get_consumers(host, port, username, password, https)
    print "\nget_consumers = "
    print json.dumps(retval, sort_keys=True, indent=4, separators=(',', ': '))

    retval = get_entitlements(host, port, username, password, https)
    print "\nget_entitlements = "
    print json.dumps(retval, sort_keys=True, indent=4, separators=(',', ': '))

    retval = get_owners(host, port, username, password, https)
    print "\nget_owners = "
    print json.dumps(retval, sort_keys=True, indent=4, separators=(',', ': '))

    pools = get_pools(host, port, username, password, https)
    print "\nget_pools = "
    for p in pools:
        print "%s\n" % p

    products = get_products(host, port, username, password, https)
    print "\nget_products = "
    for p in products:
        print "%s\n" % p

    #TODO - Need to implement support for decoding response
    #retval = get_rules(host, port, username, password, https)
    #print "\nget_rules = \n%s" % (retval)

    retval = get_subscriptions(host, port, username, password, https)
    print "\nget_subscriptions() = "
    #print json.dumps(retval, sort_keys=True, indent=4, separators=(',', ': '))
