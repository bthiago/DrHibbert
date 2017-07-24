#!/usr/bin/python

##### INCIDENT STATUS #######
#  Status	Name	Description
#
#  0 Scheduled This status is reserved for a scheduled status.
#  1 Investigating You have reports of a problem and you're currently looking into them.
#  2 Identified You've found the issue and you're working on a fix.
#  3 Watching You've since deployed a fix and you're currently watching the situation.
#  4 Fixed The fix has worked, you're happy to close the incident.
#
#############################

##### COMPONENT STATUS ######
#  Status	Name	Description
#
#  1 Operational The component is working.
#  2 Performance Issues The component is experiencing some slowness.
#  3 Partial Outage The component may not be working for everybody. This could be a geographical issue for example.
#  4 Major Outage The component is not working for anybody.
#
#############################


import os
import requests
from requests.auth import HTTPBasicAuth
import json

class CachetClient():

    def __init__(self, token=None,server_url=None):
        self.token = os.getenv('DRHIBBERT_CACHETCLIENT_TOKEN',token)
        self.server_url = os.getenv('DRHIBBERT_CACHETCLIENT_URL',server_url)

    def request_headers(self):
        headers = {'user-agent': 'cachet-client/0.0.1','Content-type':'application/json','X-Cachet-Token':self.token}
        return headers

    def update_incident(self, incident_id,incident_status, message=None,component_id=None, component_status=None):
        m = {}
        if component_id and component_status:
            m['component_id'] = component_id
            m['component_status'] = component_status
        m['status'] = incident_status
        m['visible'] = 1       

        if message:
            m['message'] = message

        url = '%s/api/v1/incidents/%s' % (self.server_url,incident_id)

        d = json.dumps(m)
        r = requests.put(url, headers=self.request_headers(), data=d)
        if r.status_code == 200:
            return json.loads(r.text)['data']
        else:
            raise Exception(r.text)

    def update_component(self, component_id, component_status):
        m = {}
        m['status'] = component_status

        url = '%s/api/v1/components/%s' % (self.server_url,component_id)

        d = json.dumps(m)
        r = requests.put(url, headers=self.request_headers(), data=d)
        if r.status_code == 200:
            return json.loads(r.text)['data']
        else:
            raise Exception(r.text)

    def find_incidents(self, status=None, name=None, component_id=None):
        url = '%s/api/v1/incidents?' % (self.server_url)
        if status:
            url = url + '&status=%s' % ( status )
        if component_id:
            url = url + '&component_id=%s' % ( component_id )
        if name:
            url = url + '&name=%s' % ( name )
        r = requests.get(url, headers=self.request_headers())
        if r.status_code == 200:
            resp_json = json.loads(r.text)
            if resp_json['data']:
                return resp_json['data']
            else:
                return None
        else:
            raise Exception(r.text)

    def fix_incident(self,incident_name,component_name,component_group_name=None):
        c = self.find_or_create_component(component_name=component_name,component_group_name=component_group_name)
        cid = c['id']
        inci = self.find_incidents(name=incident_name,component_id=cid,status='1')
        r = None
        if inci:
            for i in inci:
                r=self.update_incident(incident_status=4, component_id=cid,incident_id=i['id'])
        else:
            raise Exception('Incident not found: Name=%s; Component=%s' % (incident_name, component_name))       

        inci = self.find_incidents(component_id=cid,status='1')
        if not inci:
           self.update_component(component_id=cid,component_status='1')
        return r


    def create_incident(self, component_id, name, component_status, incident_status, message):
        m = {}
        m['component_id'] = component_id
        m['component_status'] = component_status
        m['status'] = incident_status
        m['visible'] = 1       
        m['message'] = message
        m['name'] = name

        url = '%s/api/v1/incidents' % (self.server_url)

        d = json.dumps(m)
        r = requests.post(url, headers=self.request_headers(), data=d)
        if r.status_code == 200:
            return json.loads(r.text)['data']
        else:
            raise Exception(r.text)

    def report_incident(self, component_name, incident_name, message, component_group_name=None):
        cid = self.find_or_create_component(component_name=component_name, component_group_name=component_group_name)['id']
        return self.create_incident(component_id=cid, name=incident_name, component_status=2, incident_status=1, message=message)

    def create_component_group(self, name):
        m = {}
        m['name'] = name

        url = '%s/api/v1/components/groups' % (self.server_url)

        d = json.dumps(m)
        r = requests.post(url, headers=self.request_headers(), data=d)
        if r.status_code == 200:
            return json.loads(r.text)['data']
        else:
            raise Exception(r.text)

    def find_or_create_component_group(self, component_group_name):
        url = '%s/api/v1/components/groups?name=%s' % (self.server_url,component_group_name)
        r = requests.get(url, headers=self.request_headers())
        if r.status_code == 200:
            resp_json = json.loads(r.text)
            if not resp_json['data']:
                return self.create_component_group(component_group_name)
            else:
                return resp_json['data'][0]
        else:
            raise Exception(r.text)

    def create_component(self, name, description=None,component_group_name=None):
        m = {}
        m['name'] = name
        if description:
            m['description'] = description
        if component_group_name:
            g = self.find_or_create_component_group(component_group_name)
            m['group_id'] = g['id']
        m['status'] = 1

        url = '%s/api/v1/components' % (self.server_url)

        d = json.dumps(m)
        r = requests.post(url, headers=self.request_headers(), data=d)
        if r.status_code == 200:
            return json.loads(r.text)['data']
        else:
            raise Exception(r.text)

    def find_or_create_component(self, component_name, component_group_name=None,component_description=None):
        url = '%s/api/v1/components?name=%s' % (self.server_url,component_name)
        if component_group_name:
            g = self.find_or_create_component_group(component_group_name)
            url = '%s/api/v1/components?name=%s&group_id=%s' % (self.server_url,component_name,g['id'])
        r = requests.get(url, headers=self.request_headers())
        if r.status_code == 200:
            resp_json = json.loads(r.text)
            if not resp_json['data']:
                return self.create_component(name=component_name, component_group_name=component_group_name,description=component_description)
            else:
                return resp_json['data'][0]
        else:
            raise Exception(r.text)

