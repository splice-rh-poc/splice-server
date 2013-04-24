#!/usr/bin/env python

import httplib
import time
import oauth2 as oauth 

KEY = 'WRONG_KEY'
SECRET = 'WRONG_SECRET'
URL = "https://localhost/splice/api/v1/ping/"

connection = httplib.HTTPSConnection("localhost", "443")
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
