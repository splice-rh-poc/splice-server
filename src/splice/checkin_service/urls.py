from django.conf.urls import patterns, include, url
from tastypie.api import Api
from splice.common import identity
from splice.entitlement.apis import EntitlementResource

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

v1_api = Api(api_name='v1')
v1_api.register(EntitlementResource())

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'checkin_service.views.home', name='home'),
    # url(r'^checkin_service/', include('checkin_service.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    (r'^api/', include(v1_api.urls)),
)

# Synchronize our data with rhic_serve
identity.sync_from_rhic_serve()