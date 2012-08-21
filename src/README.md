Splice Server: Checkin Service:
===============================

Planned Top level directories:
----------------------
 * checkin_service - main site django code
 * entitlement - REST API django app for receiving an entitlement certificate
 * reporting   - REST API django app for receiving reporting info from a child
 * identity    - REST API django app for querying for identify from a child

entitlement
-----------
 
Responsible for servicing entitlement certificate calls from a consumer.  

Consumer will check in hourly with us, giving us a list of installed products and an identify certificate.  We will talk to the entitlement service and determine what products shall be entitled and give back an entitlement certificate valid for a short duration.

reporting
-----------
Responsible for receiving product usage information from children

identity
--------
Responsible for returning identify information (consisting of subscription information) about a consumer, or querying up the chain of parents to see who has information on the identity.


3rd Party Software Requirements:
--------------------------------
 * django
 * django-tastypie, django-tastypie-mongoengine
 * mongo, pymongo
 * mongoengine

