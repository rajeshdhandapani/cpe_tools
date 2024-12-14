import os
import time
import requests
import unittest
import json
import datetime
import pytest

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

device_id    = "86e11097bd848f4a"
br30_bulb_id = "89f60cdc7eebb95a"
ota_bulb_id  = "8380a0dd6c35ff66"

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

    def get_metadevices(self, token, account_id,  test_device_id=None):
        u = 'https://semantics2.afero.net/v1/accounts/%s/metadevices' % (account_id)
        print (u)
        if test_device_id==None:
            test_device_id = device_id
        result = None
        query_params = {"deviceId":test_device_id}
        for i in range (1,4):
            try:
                result = requests.get(u, headers=self.get_headers_common(token),params=query_params)
            except Exception as e:
                print ("exception while calling semantics api to get metadevices! ",e)

            if result!=None:
                if result.status_code == 200:
                    break
            time.sleep(3)


        return result

    def get_auth_token(self):
        result = None
        for i in range (1,4):
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
            try:
                result = requests.post(url,data=post_data,headers=headers)
            except Exception as e:
                print ("exception while calling auth api to get token! ",e)


            if result!=None:
                if result.status_code == 200:
                    break
            time.sleep(3)
        # self.assertEqual(result.status_code, 200, "non 200 response while calling auth api to get token! ")
        return result


    def get_device_and_token(self,test_device_id=None):
        res = self.get_auth_token()

        token = res.json()['access_token']
        self.assertIsNotNone(token, "Failed to get token!")
        res = self.get_metadevices(token, account_id, test_device_id=test_device_id)
        # self.assertEqual(res.status_code, 200, "non 200 response while calling semantics api to get metadevices! ")
        devices  = res.json()
        # print (devices)

        if res.status_code == 404:
            print ("didn't get back any devices from semantics api!, status 404")
            return token, "None"
        if len(devices) == 0:
            print ("didn't get back any devices from semantics api!")
            return token, "None"
        self.assertEqual(len(devices), 1, "didn't get back 1 device from semantics api!")
        metadevice_id = devices[0]['id']


        return token,metadevice_id
    def remove_metadevice_from_account(self,token,metadevice_id):

        u = "https://semantics2.afero.net/v1/accounts/%s/metadevices/%s"%(account_id,metadevice_id)
        result = None

        for i in range (1,4):
            try:
                result = requests.delete(u,headers=self.get_headers_common(token),timeout=4)
            except Exception as e:
                print ("exception while calling semantics api to remove metadevice! ",e)
            if result!=None:

                if result.status_code == 200:
                    break
            time.sleep(3)

        self.assertEqual(result.status_code, 200, "non 200 response while calling semantics api to remove metadevice! ")
        elapsed_time = str(result.elapsed.total_seconds())
        print ("Time taken to remove device from account in seconds  : ",elapsed_time)

        return elapsed_time

    def post_device_to_account(self,token,account_id,payload,expansions=[],locale="en_US",verified='true'):
        u = 'https://semantics2.afero.net/v1/accounts/%s/devices'%(account_id)
        query_params = {"expansions":expansions,"verified":verified,"locale":locale}
        for i in range (1,4):
            try:
                result = requests.post(u,headers=self.get_headers_common(token),data=payload,params=query_params,timeout=4)
            except Exception as e:
                print ("exception while calling semantics api to post device! ",e)
            if result!=None:
                print (result.status_code)
                if result.status_code == 200:
                    break
            time.sleep(3)

        self.assertEqual(result.status_code, 200, "non 200 response while calling semantics api to post device! ")
        elapsed_time = str(result.elapsed.total_seconds())

        print ("Time taken to post device to account in seconds : ",elapsed_time)
        return elapsed_time
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

    @pytest.mark.linking
    def test_linking(self):
        token, metadevice_id = self.get_device_and_token(test_device_id=ota_bulb_id)
        self.reboot_Device(token,device_id=ota_bulb_id)
        time.sleep(120)
        state = self.get_device_state(token,ota_bulb_id)
        self.assertEqual(state['deviceState']['available'],True,"device not back to available")

        self.assertEqual(state['deviceState']['visible'], True, "device not back to visible")
        self.assertEqual(state['deviceState']['linked'], True, "device not back to visible")

    def get_device_state(self,token,device_id):
        u = 'https://api2.afero.net//v1/accounts/%s/devices/%s'%(account_id,device_id)
        result = None
        for i in range (1,4):
            try:
                result = requests.get(u, headers=self.get_headers_common(token),params={"expansions":["state"]})
            except Exception as e:
                print ("exception while calling semantics api to get metadevice state! ",e)
            if result!=None:
                if result.status_code == 200:
                    break
            time.sleep(4)
        return result.json()
    def reboot_Device(self,token,device_id=ota_bulb_id,account_id="b02f5bc7-d694-426a-bb60-097fa7684660"):

        data = [{"type": "attribute_write", "attrId": 65012, "value": "01"}]
        u = 'https://api2.afero.net/v1/accounts/%s/devices/%s/requests'%(account_id,device_id)
        for i in range (1,4):
            try:
                result = requests.post(u, data=json.dumps(data), headers=self.get_headers_common(token))
            except Exception as e:
                print ("exception while calling semantics api to post device! ",e)
            if result!=None:
                if result.status_code == 202:
                    break
            time.sleep(3)

    @pytest.mark.association
    def test_disassociate_and_associate(self):

        elapsed_times_removal = []
        elapsed_times_addition = []
        for i in range (1,2):

            time.sleep(5)
            token, metadevice_id = self.get_device_and_token()
            print ("got token")

            if metadevice_id == "None":
                print ("didn't get metadevice id, so will skip removal this time!!")
            else:
                elapsed_time = self.remove_metadevice_from_account(token,metadevice_id)
                elapsed_times_removal.append(elapsed_time)
                print ("removed")
                time.sleep(5)
            payload = self.get_association_payload()
            elapsed_time = self.post_device_to_account(token, account_id, payload, verified='true')
            elapsed_times_addition.append(elapsed_time)
            print ("added back i think!")
            time.sleep(5)
            res = self.get_metadevices(token, account_id)
            self.assertEqual(res.status_code, 200, "non 200 response while calling semantics api to get metadevices after posting the device and waiting for 5 sec :o ! ")
            devices = res.json()
            self.assertEqual(len(devices), 1, "didn't get back 1 device from semantics api after adding and waiting for 5 sec!")


        print ("Time taken to remove device from account in seconds  : ",str(elapsed_times_removal))
        print ("Time taken to post device to account in seconds : ",str(elapsed_times_addition))


    # def test_attr(self):
    #     token, metadevice_id = self.get_device_and_token()
    #     print (metadevice_id)
    #     self.assertIsNotNone(metadevice_id, "didn't get the metadevice id for the device id: " + device_id)
    #     res = self.get_metadevice_semantic_state(token,metadevice_id)
    #     print (res)
    #     self.assertIsNotNone(res, "didn't get the metadevice state for the device id: " + device_id)
    #     print (res.json())

    @pytest.mark.voice
    def test_voice(self):
        token,  metadevice_id = self.get_device_and_token(test_device_id=br30_bulb_id)
        self.assertIsNotNone(metadevice_id, "didn't get the metadevice id for the device id: " + br30_bulb_id)

        print (metadevice_id)
        for i in range (1,3):
            time.sleep(5)
            self.voice_test(token,metadevice_id)


    def voice_test(self,token,metadevice_id):
        initial_state = self.get_current_on_off_state(token,metadevice_id)
        self.assertIsNotNone(initial_state, "didn't get the initial power on/off state! ")
        print(initial_state)
        on_or_off = not initial_state == "on"
        print(on_or_off)

        payload = self.create_payload_command(customData={}, metadevice_ids=[metadevice_id],
                                              command="action.devices.commands.OnOff",
                                              params={"on": on_or_off})
        self.executeCommand(token,payload)


        time.sleep(5)
        final_state = self.get_current_on_off_state(token,metadevice_id)
        print(initial_state)
        print(final_state)
        self.assertIn(initial_state, ["on", "off"], "initial state is not on or off")
        self.assertIn(final_state, ["on", "off"], "final state is not on or off")
        self.assertNotEquals(initial_state, final_state, "didn't get the final power on/off state! ")


    def create_payload_command(self, locale_country="US", locale_language="en", intent="action.devices.EXECUTE",
                               customData=None,
                               metadevice_ids=None, command=None, params=None):
        timestamp =  int(datetime.datetime.now().timestamp() * 1000)
        devices = []
        for device in metadevice_ids:
            devices.append({"customData": customData, "id": device})
        command = {"inputs": [
            {"context": {"locale_country": locale_country, "locale_language": locale_language}, "intent": intent,
             "payload": {"commands": [
                 {"devices": devices,
                  "execution": [{"command": command, "params": params}]}]}}],
                   "requestId": str(timestamp)}

        return json.dumps(command)

    def executeCommand(self,token,  payload,auth_header="Authorization"):

        u = "https://home-depot-prod-actions.uc.r.appspot.com/fulfillment"
        result  = None

        for i in range (1,4):
            try:
                result = requests.post(u,data=payload,headers=self.get_headers_common(token))
            except Exception as e:
                print ("exception while calling voice command run! ",e)
            if result!=None:
                if result.status_code == 200:
                    break
            time.sleep(4)


        # self.assertEqual(result.status_code, 200, "didn't get back 200 from voice command run")
        time.sleep(5)
        print(result.text)
        print(result.json())


    def get_current_on_off_state(self, token,metadevice_id):
        state = self.get_metadevice_semantic_state(token,metadevice_id)
        values = state['values']
        for value in values:
            if value['functionClass'] == "power":
                return value['value']


    def get_metadevice_semantic_state(self, token,metadevice_id,):
        u = 'https://semantics2.afero.net/v1/accounts/%s/metadevices/%s/state' % (account_id, metadevice_id)
        print ( "url")
        print (u)
        result = None

        for i in range (1,4):

            try:
                result = requests.get(u, headers=self.get_headers_common(token))
            except Exception as e:
                print ("exception while calling semantics api to get metadevice state! ",e)
            if result!=None:
                if result.status_code == 200:
                    break
            time.sleep(4)


        # self.assertEqual(result.status_code, 200, "non 200 response while calling semantics api to get metadevice state! ")
        # print (result.json())
        print("Time taken to get metadevice state in seconds : ", str(result.elapsed.total_seconds()))
        return result.json()

