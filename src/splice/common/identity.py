import logging

from splice.common import config
from splice.common import rhic_serve_client
from splice.entitlement.models import ConsumerIdentity

_LOG = logging.getLogger(__name__)

def sync_from_rhic_serve():
    _LOG.info("Attempting to synchronize RHIC data from configured rhic_serve")
    cfg = config.get_rhic_serve_config_info()
    # TODO need to implement pagination
    data = rhic_serve_client.get_all_rhics(host=cfg["host"], port=cfg["port"], url=cfg["get_all_rhics_url"])
    if not data:
        _LOG.info("Received no data from %s:%s%s" % (cfg["host"], cfg["port"], cfg["get_all_rhics_url"]))
        return
    _LOG.info("Fetched %s RHICs from %s:%s%s" % (len(data), cfg["host"], cfg["port"], cfg["get_all_rhics_url"]))
    process_data(data)

def process_data(data):
    """
    Imports data into mongo, will update documents that have changed, and remove those which have been deleted

    @param data from rhic_serve in the format: [{"engineering_ids":["str_id"], "uuid":"str_id"}]
    @type [{"engineering_ids":[], "uuid":""}]
    """
    # TODO: Redo this logic so it supports batch lookups and is more efficient
    "Fetched %s rhics from rhic_serve" % (len(data))
    for item in data:
        products = item["engineering_ids"]
        uuid = item["uuid"]
        identity = ConsumerIdentity.objects(uuid=uuid).first()
        if not identity:
            create_new_consumer_identity(uuid, products)
            continue
        try:
            identity.products = products
            identity.save()
        except Exception, e:
            _LOG.exception(e)

def create_new_consumer_identity(uuid, products):
    _LOG.info("Creating new ConsumerIdentity(uuid=%s, products=%s)" % (uuid, products))
    identity = ConsumerIdentity(uuid=uuid, products=products)
    try:
        identity.save()
    except Exception, e:
        _LOG.exception(e)
