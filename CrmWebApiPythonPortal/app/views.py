"""
Definition of views.
"""

from django.shortcuts import render, redirect, render_to_response
from django.http import HttpRequest
from django.template import RequestContext
from datetime import datetime
import requests
from requests_oauthlib import OAuth2Session
from urllib.parse import quote
from django.http.response import HttpResponseRedirect
from oauthlib.oauth2 import LegacyApplicationClient
from CrmWebApiPythonPortal import settings
from app.forms import BootstrapAuthenticationForm, NewTicketForm
import json
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.contrib.auth import authenticate, get_backends, login, logout
from app.backends import ClientAuthBackend

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(request,
        'app/index.html',
        context_instance = RequestContext(request,
        {
            'title':'Home Page',
            'year':datetime.now().year,
        }))

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(request,
        'app/contact.html',
        context_instance = RequestContext(request,
        {
            'title':'Contact',
            'message':'Your contact page.',
            'year':datetime.now().year,
        }))

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(request,
        'app/about.html',
        context_instance = RequestContext(request,
        {
            'title':'About',
            'message':'Your application description page.',
            'year':datetime.now().year,
        }))

def CrmCustomerLogin(request, authentication_form):
    """Login to CRM with custom credentials prompt."""

    context = {'initialize':''}

    if request.method == 'POST':
        constants = settings.CONSTANTS
        oauth = OAuth2Session(client=LegacyApplicationClient(client_id=constants['CLIENT_ID']))
        token_dict = oauth.fetch_token(token_url=constants['TOKEN_URL'],
            username=constants['USERNAME'], password=constants['PASSWORD'],
            client_secret=constants['CLIENT_KEY'],
            verify=False,
            client_id=constants['CLIENT_ID'],
            resource=constants['RESOURCE_URI'])
            
        token = token_dict.get('access_token')
        request.session['token'] = token_dict.get('access_token')

        username = request.POST.get("username", "") 
        password = request.POST.get("password", "") 

        get_backends()
        user = authenticate(username=username, password=password, token=token, internal=False)
       
        if user != None:         
            if user.is_active:
                login(request, user)

            request.user = user
            return HttpResponseRedirect('/')
        else:
            error = "Invalid username/password"
            return render_to_response('app/CrmCustomerLogin.html', {'error': error, 
                                                                    'form': BootstrapAuthenticationForm})
    else:
        return render(request,
        'app/CrmCustomerLogin.html',
        context_instance = RequestContext(request,
        {
            'form': BootstrapAuthenticationForm
        }))  

def CrmEmployeeLogin(request):
    """Login to CRM with O365 prompt."""

    context = {'initialize':''}
    constants = settings.CONSTANTS
    azure_session = OAuth2Session(constants['CLIENT_ID'],
        redirect_uri=constants['REDIRECT_URI'])
    authorization_url, state = azure_session.authorization_url(constants['AUTHORIZATION_URL'])

    resp = requests.get(authorization_url)

    return redirect(resp.url)

def CrmWork(request):
    """Redirect URL/View - process callback after authentication."""

    context = {'initialize':''}
    constants = settings.CONSTANTS
    
    aad_code = request.GET.get('code','')

    azure_session = OAuth2Session(constants['CLIENT_ID'], redirect_uri=constants['REDIRECT_URI'])

    token_dict = azure_session.fetch_token(token_url=constants['TOKEN_URL'], 
                                        code=aad_code, 
                                        client_secret=constants['CLIENT_KEY'], 
                                        resource=constants['RESOURCE_URI'],
                                        verify =False)

    request.session['token'] = token_dict.get('access_token')

    get_backends()
    user = authenticate(token=request.session['token'], internal=True)
       
    if user != None:         
        if user.is_active:
            login(request, user)

        request.user = user

    return render(request,
        'app/index.html',
        context_instance = RequestContext(request,
        {
        }))

def Logout(request):
    """ Logout and clear session. """

    request.session['token'] = None
    logout(request)
    return redirect('/')

def CrmInvoices(request):
    """ Retrieves CRM Invoices owned by logged in employee or where customer equals logged in customer. """

    context = {'initialize':''}
    constants = settings.CONSTANTS
    headers = {'OData-MaxVersion': '4.0',
               'OData-Version': '4.0',
               'Accept': 'application/json',
               'Authorization': 'Bearer ' + request.session['token'],
               'Prefer': 'odata.include-annotations="mscrm.formattedvalue"'
              }

    if request.user.is_staff:
        response = requests.get(constants['RESOURCE_URI'] + '/api/data/invoices?$select=name,totalamount,statecode,statuscode&$filter=ownerid eq ' + request.user.userprofile.crmid, headers=headers)
    else:
        response = requests.get(constants['RESOURCE_URI'] + '/api/data/invoices?$select=name,totalamount,statecode,statuscode&$filter=customerid eq ' + request.user.userprofile.crmid, headers=headers)

    item_dict = json.loads(response.text)
    invoices = item_dict['value']

    #@odata.etag appears to break the BootstrapTable binding.
    for element in invoices: 
        del element['@odata.etag'] 
    
    return render(request, 'app/CrmInvoices.html', context_instance = RequestContext(request,
        {
            'data': json.dumps(invoices) 
        }))

def CrmInvoice(request):
    """ Retrieves an individual CRM Invoice. """

    context = {'initialize':''}
    constants = settings.CONSTANTS

    if request.method == 'GET':
        headers = {'OData-MaxVersion': '4.0',
               'OData-Version': '4.0',
               'Accept': 'application/json',
               'Authorization': 'Bearer ' + request.session['token'],
               'Prefer': 'odata.include-annotations="mscrm.formattedvalue"'
              }

        invoiceid = request.GET.get('invoiceid')

        response = requests.get(constants['RESOURCE_URI'] + '/api/data/invoices(' + invoiceid + ')?$select=name,totalamount', headers=headers)

        item_dict = json.loads(response.text)
        return render(request, 'app/CrmInvoice.html', context_instance = RequestContext(request,
            {
                'name': item_dict['name'],
                'totalamount': item_dict['totalamount@mscrm.formattedvalue']
            }))
    else:
        invoice = {}
        invoice['statecode'] = 2
        invoice['statuscode'] = 100001 
        json_data = json.dumps(invoice)

        headers = {'OData-MaxVersion': '4.0',
               'OData-Version': '4.0',
               'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + request.session['token'],
              }

        invoiceid = request.REQUEST.get("invoiceid", "") 

        response = requests.patch(constants['RESOURCE_URI'] + '/api/data/invoices(' + invoiceid + ')', data=json_data, headers=headers)

        return HttpResponseRedirect('CrmInvoices.html')

def CrmTickets(request):
    """ Retrieves Active CRM Tickets owned by logged in employee or where customer equals logged in customer. """

    context = {'initialize':''}
    constants = settings.CONSTANTS

    headers = {
               'Accept': 'application/json',
               'Authorization': 'Bearer ' + request.session['token']
              }

    if request.user.is_staff:
        response = requests.get(constants['RESOURCE_URI'] + "/XRMServices/2011/OrganizationData.svc/IncidentSet?$select=IncidentId,CustomerId,TicketNumber,Title&$filter=StateCode/Value eq 0 and OwnerId/Id eq guid'" + request.user.userprofile.crmid + "'", headers=headers)
    else:
        response = requests.get(constants['RESOURCE_URI'] + "/XRMServices/2011/OrganizationData.svc/IncidentSet?$select=IncidentId,CustomerId,TicketNumber,Title&$filter=StateCode/Value eq 0 and CustomerId/Id eq guid'" + request.user.userprofile.crmid + "'", headers=headers)
        
    item_dict = json.loads(response.text)
    d = item_dict['d']
    tickets = d['results']

    #__metadata appears to break the BootstrapTable binding.
    for element in tickets: 
        del element['__metadata']           

    return render(request, 'app/CrmTickets.html', context_instance = RequestContext(request,
        {
            'data': json.dumps(tickets) 
        }))

def CrmTicket(request):
    """ Retrieves an individual CRM Ticket. """

    context = {'initialize':''}
    constants = settings.CONSTANTS
    ticketid = request.REQUEST.get("ticketid", "")     

    if request.method == 'POST':  
        form = NewTicketForm(request.POST)
        if form.is_valid():
            ticket = {}
            ticket['title'] = form.cleaned_data.get('title')
            ticket['description'] = form.cleaned_data.get('description')
            if ticketid == "": 
                ticket['incident_customer_contacts@odata.bind'] = 'contacts(' + request.user.userprofile.crmid + ')'

            json_data = json.dumps(ticket)

            headers = {'OData-MaxVersion': '4.0',
                    'OData-Version': '4.0',
                    'Content-Type': 'application/json; charset=utf-',
                    'Authorization': 'Bearer ' + request.session['token'],
                    'accept': 'application/json'
                    }

            if ticketid == "": #New
                response = requests.post(constants['RESOURCE_URI'] + '/api/data/incidents', data=json_data, headers=headers)
            else: #Update
                response = requests.patch(constants['RESOURCE_URI'] + '/api/data/incidents(' + ticketid + ')', data=json_data, headers=headers)

        return HttpResponseRedirect('CrmTickets.html')
    else:
        if ticketid == "": 
            #New form
            form = NewTicketForm()
        
            return render(request, 'app/CrmTicket.html', {'form': form, 'is_new': True})
        else: 
            headers = {'OData-MaxVersion': '4.0',
               'OData-Version': '4.0',
               'Accept': 'application/json',
               'Authorization': 'Bearer ' + request.session['token'],
               'Prefer': 'odata.include-annotations="mscrm.formattedvalue"'
              }

            response = requests.get(constants['RESOURCE_URI'] + '/api/data/incidents(' + ticketid + ')?$select=ticketnumber,title,description', headers=headers)

            item_dict = json.loads(response.text)
        
            form = NewTicketForm({
                'title': item_dict['title'],
                'description': item_dict['description']
                })

            return render(request, 'app/CrmTicket.html', {'form': form, 'is_new': False, 'ticketnumber': item_dict['ticketnumber']})