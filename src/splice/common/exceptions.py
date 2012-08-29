import httplib
from django.http import HttpResponse

class CheckinException(Exception):
    pass

class CertValidationException(CheckinException):
    def __init__(self):
        self.response = HttpResponse(
            content="Unable to verify consumer's identity certificate was signed by configured CA",
            status=httplib.FORBIDDEN)

class UnallowedProductException(CheckinException):
    def __init__(self, consumer_uuid, products):
        super(UnallowedProductException, self).__init__(self, )
        self.consumer_uuid = consumer_uuid
        self.products = products
        self.response = HttpResponse(
            content= self.__str__(),
            status=httplib.PAYMENT_REQUIRED
        )

    def __str__(self):
        return "Consumer with uuid '%s' is not allowed to access products '%s'" % (self.consumer_uuid, self.products)

class UnknownConsumerIdentity(CheckinException):
    def __init__(self, identity):
        super(UnknownConsumerIdentity, self).__init__(self)
        self.identity = identity
        self.response = HttpResponse(
            content=self.__str__(),
            status=httplib.NOT_FOUND
        )

    def __str__(self):
        return "Unknown consumer identity '%s'" % (self.identity)

class RequestException(Exception):
    def __init__(self, status, message=""):
        super(RequestException, self).__init__()
        self.status = status
        self.message = message
        self.response = HttpResponse(
            content=self.__str__(),
            status=httplib.BAD_GATEWAY
        )

    def __str__(self):
        return "Exception: remote request yielded status code: '%s' with body '%s'"\
        % (self.status, self.message)

