from .models import CustomerLogin
from CrmWebApiPythonPortal import settings
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import LegacyApplicationClient
import requests
import json
from django.contrib.auth.models import User
from django.contrib.auth import login
from urllib.request import urlopen

class ClientAuthBackend(object):

    def authenticate(self, username=None, password=None, token=None, internal=False):
        if not internal:
            user = self.CrmValidateLoginWebApi(token, username, password)
            return user
        else:
            user = self.CrmGetUserInfo(token)
            return user

    def CrmValidateLoginWebApi(self, token, username, password):
        """ Validate custom uername & password. """

        constants = settings.CONSTANTS
        headers = {'OData-MaxVersion': '4.0',
                   'OData-Version': '4.0',
                   'Accept': 'application/json',
                   'Authorization': 'Bearer ' + token
                  }
        response = requests.get(constants['RESOURCE_URI'] + '/api/data/contacts?$select=contactid,firstname,lastname&$filter=lat_webusername eq \'' + username + '\' and lat_webpassword eq \'' + password + '\'&$top=1', headers = headers)

        item_dict = json.loads(response.text)
        count = len(item_dict['value'])

        if count == 1:
            try:
                user = User.objects.get(username=username)

                return user
            except User.DoesNotExist:
                result = item_dict['value'][0]
                user = User(username=username)
                user.is_staff = False
                user.first_name = result['firstname']
                user.last_name = result['lastname']
                user.save()
                profile = user.userprofile
                profile.crmid = result['contactid']
                profile.save()

                return user
        else:
            return None

    def CrmGetUserInfo(self, token):
        """ Get CRM user information. """

        constants = settings.CONSTANTS
        headers = {'OData-MaxVersion': '4.0',
                   'OData-Version': '4.0',
                   'Accept': 'application/json',
                   'Authorization': 'Bearer ' + token
                  }

        userId = self.CrmWhoAmIWebApi(token)

        response = requests.get(constants['RESOURCE_URI'] + '/api/data/systemusers(' + userId + ')?$select=firstname,lastname,internalemailaddress', 
                                headers=headers)

        item_dict = json.loads(response.text)

        try:
            user = User.objects.get(username=item_dict['internalemailaddress'])
            return user
        except User.DoesNotExist:
            user = User(username=item_dict['internalemailaddress'])
            user.is_staff = True
            user.first_name = item_dict['firstname']
            user.last_name = item_dict['lastname']
            user.save()
            profile = user.userprofile
            profile.crmid = item_dict['systemuserid']
            profile.save()

            return user
    
    def CrmWhoAmIWebApi(self, token):
        """ CRM WhoAmI to determine logged in user. """

        constants = settings.CONSTANTS
        headers = {'OData-MaxVersion': '4.0',
                   'OData-Version': '4.0',
                   'Accept': 'application/json',
                   'Authorization': 'Bearer ' + token
                  }
        response = requests.get(constants['RESOURCE_URI'] + '/api/data/WhoAmI', headers=headers)
        responseJson = response.json()

        userid = responseJson["UserId"]

        return userid

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None