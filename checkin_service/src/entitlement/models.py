from mongoengine import DateTimeField, Document, EmbeddedDocument, \
    EmbeddedDocumentField, ListField, ReferenceField, StringField, UUIDField
###
# Overview of what functionality will need to be supported:
# 1) A splice-consumer will checkin with us and pass us: identifier + installed engineering products
#    We will need to:
#    - convert engineering products + identifier to marketing products
#    - determine if identifier is allowed to access marketing products
#    - request entitlement certificate for allowed engineering products
#    - record usage of marketing products
# 2) A splice-server will contact us to ask if we know of a consumer identity
#    We will need to:
#    - check our database to determine if consumer identity is known
#      - if known, return the subscription information for the identity
#    - query our parent for the identity information
# 3) A splice-server will contact us to upload their reporting information
#    We will need to:
#    - accept reporting data, aggregate it with our own data and
#      keep track of path of usage through splice servers
# 4) Be able to import consumer identity information from a file based export or other splice-server
#
# Thoughts/Questions
#  - How does a SpliceServer bootstrap itself on initial setup?
#       - Would the top level entity issue a certificate with a splice server UUID
#       on first-initialization certificate is parsed to determine splice-server UUID
#
#       OR
#
#       - Do we go with a more decentralized approach, where we create our own uuid, then propogate this UUID
#       and the parent/child chain information with our reporting data?
#           Question is from the perspective when we are looking at the reporting data, how do we determine where
#           the usage came from.  Do we look at the chain of parent-child-child-...  or do we assume a splice-server
#           UUID is sufficient?
###

class SpliceServer(Document):
    uuid = UUIDField(required=True, unique=True)
    description = StringField() # Example what datacenter is this deployed to, i.e. us-east-1
    hostname = StringField(required=True)

class SpliceServerRelationships(Document):
    self = ReferenceField(SpliceServer, required=True)
    parent = ReferenceField(SpliceServer)
    children = ListField(ReferenceField(SpliceServer))

class MarketingProduct(Document):
    uuid = UUIDField(required=True, unique=True)
    name = StringField(required=True)
    description = StringField()

class MarketingProductSubscription(EmbeddedDocument):
    expires = DateTimeField(required=True)
    product = ReferenceField(MarketingProduct, required=True)

class ConsumerIdentity(Document):
    uuid = UUIDField(required=True, unique=True)  # matches the identifier from the identity certificate
    subscriptions = ListField(EmbeddedDocumentField(MarketingProductSubscription))

class ReportingItem(EmbeddedDocument):
    product = ReferenceField(MarketingProduct, required=True)
    date = DateTimeField(required=True)

class ProductUsage(Document):
    consumer = ReferenceField(ConsumerIdentity)
    splice_server = ReferenceField(SpliceServer, required=True)
    instance_identifier = StringField(required=True, unique_with=["splice_server"]) # example: MAC Address
    usage = ListField(EmbeddedDocumentField(ReportingItem))

    


