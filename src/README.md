Splice Server: Checkin Service:
===============================

Planned Top level directories:
----------------------
 * checkin_service - main site django code
 * entitlement - REST API django app for receiving an entitlement certificate
 * common      - Helper modules to share between djagno apps

entitlement
-----------
 
Responsible for servicing entitlement certificate calls from a consumer.  

Consumer will check in hourly with us, giving us a list of installed products and an identify certificate.  We will talk to the entitlement service and determine what products shall be entitled and give back an entitlement certificate valid for a short duration.

3rd Party Software Requirements:
--------------------------------
 * django
 * django-tastypie, django-tastypie-mongoengine
 * mongo, pymongo
 * mongoengine
 * Apache & mod_wsgi & mod_ssl

