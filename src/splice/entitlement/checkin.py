# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


import logging
import time
import pytz

from datetime import datetime, timedelta
from uuid import UUID

from splice.common import candlepin_client, utils
from splice.common.certs import CertUtils
from splice.common.config import CONFIG, get_candlepin_config_info, get_splice_server_info
from splice.common.exceptions import CheckinException, CertValidationException, UnallowedProductException, \
    UnknownConsumerIdentity, DeletedConsumerIdentityException, NotFoundConsumerIdentity, UnexpectedStatusCodeException
from splice.common.identity import sync_from_rhic_serve
from splice.entitlement.models import ConsumerIdentity, ProductUsage, SpliceServer
from splice.managers import identity_lookup

_LOG = logging.getLogger(__name__)

SPLICE_SERVER_INFO = get_splice_server_info()

class CheckIn(object):
    """
    Logic for recording a consumers usage and returning an entitlement certificate
    will be implemented here.
    """
    def __init__(self):
        self.cert_utils = CertUtils()
        f = None
        try:
            self.root_ca_path = CONFIG.get("security", "root_ca_cert")
            f = open(self.root_ca_path, "r")
            self.root_ca_cert_pem = f.read()
        finally:
            if f:
                f.close()

    def get_this_server(self):
        # parse a configuration file and determine our splice server identifier
        # TODO  read in a SSL cert that identifies our splice server.
        server_uuid = SPLICE_SERVER_INFO["uuid"]
        hostname = SPLICE_SERVER_INFO["hostname"]
        environment = SPLICE_SERVER_INFO["environment"]
        description = SPLICE_SERVER_INFO["description"]
        server = SpliceServer.objects(uuid=server_uuid).first()
        if not server:
            server = SpliceServer(
                uuid=server_uuid,
                description=description,
                hostname=hostname,
                environment=environment
            )
            try:
                server.save()
            except Exception, e:
                _LOG.exception(e)
        return server

    def get_entitlement_certificate(self, identity_cert, consumer_identifier,
                                    facts, installed_products, cert_length_in_min=None):
        """
        @param identity_cert: str containing X509 certificate, identify of the consumer
        @type identity_cert: str

        @param consumer_identifier: a str to help uniquely identify consumers in a given network, could be MAC address
        @type consumer_identifier: str

        @param facts info about the hardware from the consumer, memory, cpu, etc
        @type facts: {}

        @param installed_products: a list of X509 certificates, identifying each product installed on the consumer
        @type products: [str]

        @return:    tuple
                    first tuple item is a a list of tuples,
                        first entry is a string of the x509 certificate in PEM format,
                        second entry is the associated private key in string format,
                    next tuple item is an integer representing how long the
                    entitlement service took to process the call
        @rtype: [(str,str)], int
        """
        if not self.validate_cert(identity_cert):
            raise CertValidationException()

        identity = self.get_identity(identity_cert)

        # installed_products - product certificates installed on consumer
        # allowed_products - products allowed by identity
        # unallowed_products - products installed on consumer but unallowed by identity

        allowed_products, unallowed_products = self.check_access(identity, installed_products)
        if unallowed_products:
            _LOG.info("%s requested access to unallowed products: '%s'" % (identity, unallowed_products))

        cert_info, ent_call_time = self.request_entitlement(identity, cert_length_in_min)
        self.record_usage(identity, consumer_identifier, facts, allowed_products, unallowed_products)
        return cert_info, ent_call_time

    def validate_cert(self, cert_pem):
        """
        @param cert_pem: x509 encoded pem certificate as a string
        @param cert_pem: str

        @return: true if 'cert_pem' was signed by the configured root CA, false otherwise
        @rtype: bool
        """
        _LOG.info("Validate the identity_certificate is signed by the expected CA from '%s'" % (self.root_ca_path))
        _LOG.debug(cert_pem)
        return self.cert_utils.validate_certificate_pem(cert_pem, self.root_ca_cert_pem)

    def extract_id_from_identity_cert(self, identity_cert):
        subj_pieces = self.cert_utils.get_subject_pieces(identity_cert)
        if subj_pieces and subj_pieces.has_key("CN"):
            return subj_pieces["CN"]
        return None

    def get_identity(self, identity_cert):
        id_from_cert = self.extract_id_from_identity_cert(identity_cert)
        return self.get_identity_object(id_from_cert)

    def get_identity_object(self, consumer_uuid):
        _LOG.info("Found ID from identity certificate is '%s' " % (consumer_uuid))
        identity = ConsumerIdentity.objects(uuid=UUID(consumer_uuid)).first()
        if not identity:
            # Lookup if we have a cached response for this uuid
            cached_status_code = identity_lookup.get_cached_status_code(consumer_uuid)
            if cached_status_code:
                _LOG.info("Found cached lookup for '%s' with status_code '%s'" % (consumer_uuid, cached_status_code))
                if cached_status_code == 404:
                    raise NotFoundConsumerIdentity(consumer_uuid)
                else:
                    raise UnexpectedStatusCodeException(consumer_uuid, cached_status_code)
            # If not, create a new lookup and query parent
            _LOG.info("Couldn't find RHIC with ID '%s', will query parent" % (consumer_uuid))
            identity_lookup.create_rhic_lookup_task(consumer_uuid)
            raise UnknownConsumerIdentity(consumer_uuid)
        return identity

    def check_access(self, identity, installed_products):
        """
        @param identity the consumers identity
        @type identity: splice.common.models.ConsumerIdentity

        @param installed_products list of product ids representing the installed engineering products
        @type installed_products: [str, str]]

        @return tuple of list of allowed products and list of unallowed products
        @rtype [],[]
        """
        _LOG.info("Check if consumer identity <%s> is allowed to access products: %s" % \
                  (identity, installed_products))
        if identity.deleted:
            _LOG.info("check_access() found that consumer identifier: %s has been deleted" % (identity.uuid))
            raise DeletedConsumerIdentityException(identity.uuid)

        allowed_products = []
        unallowed_products = []
        for prod in installed_products:
            if prod not in identity.engineering_ids:
                unallowed_products.append(prod)
            else:
                allowed_products.append(prod)
        return allowed_products, unallowed_products

    def record_usage(self, identity, consumer_identifier, facts, allowed_products, unallowed_products):
        """
        @param identity consumer's identity
        @type identity: str

        @param consumer_identifier means of uniquely identifying different instances with same consumer identity
            an example could be a mac address
        @type consumer_identifier: str

        @param facts system facts
        @type facts: {}

        @param allowed_products:    list of product ids that are
                                    installed and entitled for usage by consumer
        @type allowed_products: [str]

        @param unallowed_products:  list of product ids that are
                                    installed but _not_ entitled for usage by consumer
        @type unallowed_products: [str]
        """
        try:
            sanitized_facts = utils.sanitize_dict_for_mongo(facts)
            _LOG.info("Record usage for '%s' with "
                        "allowed_products '%s', "
                        "unallowed_products '%s' "
                        "on instance with identifier '%s' and facts <%s>" %\
                (identity, allowed_products, unallowed_products,
                 consumer_identifier, sanitized_facts))
            consumer_uuid_str = str(identity.uuid)
            prod_usage = ProductUsage(consumer=consumer_uuid_str, splice_server=self.get_this_server(),
                instance_identifier=consumer_identifier,
                allowed_product_info=allowed_products,
                unallowed_product_info=unallowed_products,
                facts=sanitized_facts,
                date=datetime.now())
            prod_usage.save()
        except Exception, e:
            _LOG.exception(e)
        return

    def request_entitlement(self, identity, cert_length_in_min=None):
        """
        Will request an entitlement certificate for all engineering_ids associated
        to this 'identity'.

        @param identity: the identity requesting an entitlement certificate
        @type identity: checkin_service.entitlement.models.ConsumerIdentity
        @param cert_length_in_min:  optional param, if specified will ask
                                    candlepin for a cert that will live for
                                    this many minutes
        @type cert_length_in_min: int
        @return: Certificate and the time it took for entitlement server to process the call
        @rtype: str, int
        """
        cp_config = get_candlepin_config_info()
        start_date=None
        end_date=None
        if cert_length_in_min:
            start_date = datetime.now(tz=pytz.utc)
            end_date = start_date + timedelta(minutes=cert_length_in_min)
            start_date = start_date.isoformat()
            end_date = end_date.isoformat()

        _LOG.info("Request entitlement certificate from external service: %s:%s%s for RHIC <%s> with products <%s>" %\
                    (cp_config["host"], cp_config["port"], cp_config["url"], identity.uuid, identity.engineering_ids))

        start_time = time.time()
        cert_info = candlepin_client.get_entitlement(
            host=cp_config["host"], port=cp_config["port"], url=cp_config["url"],
            requested_products=identity.engineering_ids,
            identity=str(identity.uuid),
            username=cp_config["username"], password=cp_config["password"],
            start_date=start_date, end_date=end_date)
        end_time = time.time()
        return cert_info, end_time - start_time

