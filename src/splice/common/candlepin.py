#!/usr/bin/env python

from splice.common import candlepin_client, config
from splice.common.models import Pool, Product


def sync_pools():
    cfg = config.get_candlepin_config_info()
    pools = candlepin_client.get_pools(host=cfg["host"], port=cfg["port"], username=cfg["username"],
                                password=cfg["password"], https=cfg["https"], baseurl=cfg["url"])
    for p in pools:
        found = Pool.objects(product_id=p.product_id).first()
        if found:
            if found.updated < p.updated:
                found.update_to(p)
                found.update()
        else:
            p.save()

    objs = Pool.objects().only("product_id").all()
    db_product_ids = set([x.product_id for x in objs])
    source_product_ids = set([x.product_id for x in pools])
    to_delete_ids = db_product_ids - source_product_ids
    for p_id in to_delete_ids:
        p = Pool.objects(product_id=p_id).first()
        p.delete()


def sync_products():
    cfg = config.get_candlepin_config_info()
    products = candlepin_client.get_products(host=cfg["host"], port=cfg["port"], username=cfg["username"],
                                   password=cfg["password"], https=cfg["https"], baseurl=cfg["url"])
    for p in products:
        found = Product.objects(product_id=p.product_id).first()
        if found:
            if found.updated < p.updated:
                found.update_to(p)
                found.update()
        else:
            p.save()

    objs = Product.objects().only("product_id").all()
    db_product_ids = set([x.product_id for x in objs])
    source_product_ids = set([x.product_id for x in products])
    to_delete_ids = db_product_ids - source_product_ids
    for p_id in to_delete_ids:
        p = Pool.objects(product_id=p_id).first()
        p.delete()


def sync_all():
    sync_pools()
    sync_products()

if __name__ == "__main__":
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "splice.checkin_service.settings")

    from django.conf import settings
    config.init(settings.SPLICE_CONFIG_FILE)

    sync_all()
