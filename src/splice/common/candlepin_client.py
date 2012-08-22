# Responsible for making a remote call to candlepin and retrieve an entitlement certificate

import base64
import httplib
import json
import time
import urllib

class RequestException(Exception):
    def __init__(self, status, message=""):
        super(RequestException, self).__init__()
        self.status = status
        self.message = message

    def __str__(self):
        return "Exception: request yielded status code: '%s' with body '%s'" \
        % (self.status, self.message)

def get_entitlement(host, port, url, installed_product, identity,
                    username, password, debug=False):
    status, data = _request(host, port, url, installed_product, identity,
        username, password, debug)
    if status == 200:
        return parse_data(data)
    raise RequestException(status, data)

def parse_data(data):
    ret_value = []
    for item in data:
        product_info = {}
        product_info["certs"] = []
        for d in item["certificates"]:
            c = {}
            c["cert"] = d["cert"]
            c["key"] = d["key"]
            product_info["certs"].append(c)
        product_info["product_id"] = item["pool"]["productId"]
        product_info["product_name"] = item["pool"]["productName"]
        ret_value.append(product_info)
    return ret_value

def _request(host, port, url, installed_product,
                identity, username, password, debug=False):
    connection = httplib.HTTPConnection(host, port)
    if debug:
        connection.set_debuglevel(100)
    method = 'GET'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    raw = ':'.join((username, password))
    encoded = base64.encodestring(raw)[:-1]
    headers['Authorization'] = 'Basic ' + encoded

    query_params = {
        "installed": installed_product,
        "rhic": identity,
    }
    data = urllib.urlencode(query_params)
    url = url +"?" + data
    connection.request(method, url, body=None, headers=headers)

    response = connection.getresponse()
    response_body = response.read()
    if response.status == 200:
        response_body_raw = response_body
        response_body = json.loads(response_body_raw)
        if debug:
            print "Response: %s %s" % (response.status, response.reason)
            print "JSON: %s" % (json.dumps(response_body))
            output = open("example_candlepin_data_%s.json" % (time.time()), "w")
            output.write(response_body_raw)
            output.close()
    return response.status, response_body

if __name__ == "__main__":
    print get_entitlement(host="localhost", port=8080, url="/candlepin/splice/cert",
        installed_product="37060!Awesome OS Workstation",
        identity="admin",
        username="admin", password="admin", debug=True)
