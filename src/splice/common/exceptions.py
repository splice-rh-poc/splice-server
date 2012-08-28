class CheckinException(Exception):
    pass

class CertValidationException(CheckinException):
    pass

class UnallowedProductException(CheckinException):
    def __init__(self, products):
        super(UnallowedProductException, self).__init__(self)
        self.products = products

    def __str__(self):
        return "Unallowed products: %s" % (products)

class UnknownConsumerIdentity(CheckinException):
    def __init__(self, identity):
        super(UnknownConsumerIdentity, self).__init__(self)
        self.identity = identity

    def __str__(self):
        return "Unknown consumer identity '%s'" % (self.identity)

class RequestException(Exception):
    def __init__(self, status, message=""):
        super(RequestException, self).__init__()
        self.status = status
        self.message = message

    def __str__(self):
        return "Exception: request yielded status code: '%s' with body '%s'"\
        % (self.status, self.message)

