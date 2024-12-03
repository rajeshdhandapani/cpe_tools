import os
import time
import requests
import unittest
import json

password_field = 'thd_automation_password'
password = "default"
secret = "default"
if password_field in os.environ:
    password = os.getenv(password_field)

env = "thd"


secret_field = 'thd_automation_client_secret'
if secret_field in os.environ:
    secret = os.getenv(secret_field)

account_email = "thdmonitor@afero.io"





account_id="b02f5bc7-d694-426a-bb60-097fa7684660"
device_id = "86e11097bd848f4a"
association_id = "default"

association_field = 'thd_device_association_id'
if association_field in os.environ:
    association_id = os.getenv(association_field)



#
# payload = semanticsApi.create_payload_for_association(association_id,device_id)
# res = semanticsApi.post_device_to_account(token, account_id, payload,verified=True)

class ThdMonitor(unittest.TestCase):

    def get_headers_common(self,token):
        headers = {'accept':'*/*',
                   'Content-Type': 'application/json',"Authorization": f"Bearer {token}"}
        return headers

    def get_metadevices(self, token, account_id,  device_id):
        u = 'https://semantics2.afero.net/v1/accounts/%s/metadevices' % (account_id)
        print (u)
        query_params = {"deviceId":device_id}

        result = requests.get(u, headers=self.get_headers_common(token),params=query_params)
        print (result.status_code)
        return result

    def get_auth_token(self):

        url = "https://accounts.hubspaceconnect.com/auth/realms/thd/protocol/openid-connect/token"

        post_data = {"client_id": "test-thd-automation",
                     "grant_type": "password",
                     "client_secret": secret,
                     "scope": "openid",
                     "username": account_email,
                     "password": password}
        headers = {"Content-Type": "application/x-www-form-urlencoded",
                             'Accept': '*/*',
                             'User-Agent': 'Runsuite Automated Test Driver'}
        result = requests.post(url,data=post_data,headers=headers)
        self.assertEqual(result.status_code, 200, "non 200 response while calling auth api to get token! ")
        print (result.status_code)
        return result


    def get_device_and_token(self):
        res = self.get_auth_token()
        token = res.json()['access_token']
        self.assertIsNotNone(token, "Failed to get token!")
        res = self.get_metadevices(token, account_id, device_id)
        self.assertEqual(res.status_code, 200, "non 200 response while calling semantics api to get metadevices! ")
        devices  = res.json()
        self.assertEqual(1,len(devices),"Expected only 1 device but got "+str(len(devices)))
        metadevice_id = devices[0]['id']

        return token,metadevice_id
    def remove_metadevice_from_account(self,token,metadevice_id):
        u = "https://semantics2.afero.net/v1/accounts/%s/metadevices/%s"%(account_id,metadevice_id)
        result = requests.delete(u,headers=self.get_headers_common(token))
        self.assertEqual(result.status_code, 200, "non 200 response while calling semantics api to remove metadevice! ")
        return result

    def post_device_to_account(self,token,account_id,payload,expansions=[],locale="en_US",verified='true'):
        u = 'https://semantics2.afero.net/v1/accounts/%s/devices'%(account_id)
        query_params = {"expansions":expansions,"verified":verified,"locale":locale}
        result = requests.post(u,headers=self.get_headers_common(token),data=payload,params=query_params)
        self.assertEqual(result.status_code, 200, "non 200 response while calling semantics api to post device! ")
        return result
    def get_association_payload(self,latitude=0.0,longitude=0.0,timezone="America/Los_Angeles"):
        payload = {
        "associationId": "1:%s:%s"%(association_id,device_id),
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },
        "timezone": timezone
        }
        return json.dumps(payload)

    def test_disassociate_and_associate(self):
        token,  metadevice_id = self.get_device_and_token()
        print (token)
        self.remove_metadevice_from_account(token,metadevice_id)
        time.sleep(2)
        payload = self.get_association_payload()
        self.post_device_to_account(token, account_id, payload, verified='true')



