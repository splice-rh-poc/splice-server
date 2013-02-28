#!/usr/bin/env python
import json
import os
import sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "splice.checkin_service.settings")

from optparse import OptionParser
from splice.common import candlepin_client, utils

def get_pools(host, port, username, password, https):
    return candlepin_client.get_pools(host, port, username, password, https)


def get_products(host, port, username, password, https):
    return candlepin_client.get_products(host, port, username, password, https)


def get_rules(host, port, username, password, https):
    return candlepin_client.get_rules(host, port, username, password, https)

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


    pools = get_pools(host, port, username, password, https)
    pools_json = utils.obj_to_json(pools, indent=2)
    pools_file = open("./pools.json", "w")
    try:
        pools_file.write("{\"objects\": ")
        pools_file.write(pools_json)
        pools_file.write("}")
    finally:
        pools_file.close()

    products = get_products(host, port, username, password, https)
    products_json = utils.obj_to_json(products, indent=2)
    products_file = open("./products.json", "w")
    try:
        products_file.write("{\"objects\": ")
        products_file.write(products_json)
        products_file.write("}")
    finally:
        products_file.close()

    rules = get_rules(host, port, username, password, https)
    rules_json = utils.obj_to_json(rules, indent=2)
    rules_file = open("./rules.json", "w")
    try:
        rules_file.write("{\"objects\": [")
        rules_file.write(rules_json)
        rules_file.write("]}")
    finally:
        rules_file.close()


