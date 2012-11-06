REST API
========

.. toctree::
   :maxdepth: 2

.. http:post:: /api/v1/entitlement/(str:uuid)/

   Process a splice checkin and request an entitlement cert for installed
   products.

   **Sample request**:

   .. sourcecode:: http

      POST /api/v1/entitlement/(str:uuid)/ HTTP/1.1
      Host: example.com
      Accept: application/json

      {
        'consumer_identifier': '52:54:00:15:E7:69',
        'products': ['40', '41'],
        'system_facts': {'tbd': 'values'}
      }
  
   **Sample Response**:

   .. sourcecode:: http

      HTTP/1.0 200 OK
      Content-Type: application/json

      {
        'certs': [[<Entitlement Certificate Value>]],
         'consumer_identifier': '52:54:00:15:E7:69',
         'message': '',
         'products': ['40', '41'],
         'resource_uri': '',
         'system_facts': {'tbd': 'values'}
      }

   :statuscode 200: Ok
