"""
Definition of urls for CrmWebApiPythonPortal.
"""

from datetime import datetime
from django.conf.urls import patterns, url
from app.forms import BootstrapAuthenticationForm

# Uncomment the next lines to enable the admin:
# from django.conf.urls import include
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'app.views.home', name='home'),
    url(r'^contact$', 'app.views.contact', name='contact'),
    url(r'^about', 'app.views.about', name='about'),
    url(r'^CrmCustomerLogin/$',
        'app.views.CrmCustomerLogin',
        {
            'authentication_form': BootstrapAuthenticationForm,
        },
        name='CrmCustomerLogin'),
    #url(r'^logout$',
    #    'django.contrib.auth.views.logout',
    #    {
    #        'next_page': '/',
    #    },
    #    name='logout'),
    url(r'^CrmEmployeeLogin', 'app.views.CrmEmployeeLogin', name='CrmEmployeeLogin'),
    url(r'^CrmWork', 'app.views.CrmWork', name='CrmWork'),
    url(r'^Logout', 'app.views.Logout', name='Logout'),
    url(r'^CrmInvoices', 'app.views.CrmInvoices', name='CrmInvoices'),
    url(r'^CrmInvoice', 'app.views.CrmInvoice', name='CrmInvoice'),
    url(r'^CrmTickets', 'app.views.CrmTickets', name='CrmTickets'),
    url(r'^CrmTicket', 'app.views.CrmTicket', name='CrmTicket'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
