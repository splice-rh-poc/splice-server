#!/usr/bin/env python

import httplib
import time
import oauth2 as oauth 

X509_KEY = "/etc/pki/splice/Splice_testing_root_CA.key"
X509_CERT = "/etc/pki/splice/Splice_testing_root_CA.crt"

KEY = 'example-key'
SECRET = 'example-secret'
URL = "https://localhost/splice/api/v1/ping/"

connection = httplib.HTTPSConnection("localhost", "443", key_file=X509_KEY, cert_file=X509_CERT)
consumer = oauth.Consumer(KEY, SECRET)
method = "PUT"

oauth_request = oauth.Request.from_consumer_and_token(consumer, http_method=method, http_url=URL)
oauth_request.sign_request(oauth.SignatureMethod_HMAC_SHA1(), consumer, None)

headers = oauth_request.to_header()
connection.request(method, "/splice/api/v1/ping/", headers=headers) 
response = connection.getresponse()

print "headers: %s" % (headers)
print "Status: %s" % (response.status)
print "Reason: %s" % (response.reason)
print "Body: %s" % (response.read())
