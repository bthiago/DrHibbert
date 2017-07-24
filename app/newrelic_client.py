#!/usr/bin/python

import os
import requests
from requests.auth import HTTPBasicAuth
import json

class NewRelicClient():

    def __init__(self,server_url=None, token=None, channel_id=None):
        self.token = os.getenv('DRHIBBERT_NEWRELICCLIENT_TOKEN',token)
        self.server_url = os.getenv('DRHIBBERT_NEWRELICCLIENT_URL',server_url)
        self.channel_id = os.getenv('DRHIBBERT_NEWRELICCLIENT_CHANNEL_ID',channel_id)

    def request_headers_get(self):
        headers = {'user-agent': 'newrelic-client/0.0.1','X-Api-Key':self.token}
        return headers

    def request_headers_post(self):
        headers = {'user-agent': 'newrelic-client/0.0.1','X-Api-Key':self.token, 'Content-type':'application/json'}
        return headers

    def apm_create_alarm_response_time(self, app_name, operator='above', threshold='0.5'):
        self.apm_create_alarm(app_name,'response_time_web', operator, threshold)

    def apm_create_alarm_error_rate(self, app_name, operator='above', threshold='1'):
        self.apm_create_alarm(app_name,'error_percentage', operator, threshold)

    def apm_create_alarm(self, app_name, metric_name, operator, threshold):

        url = '%s/v2/applications.json' % (self.server_url)
        d = '?filter[name]=%s' % (app_name)
        url = url + d
        r = requests.get(url, headers=self.request_headers_get())
        application = None
        if r.status_code == 200:
            applications = json.loads(r.text)['applications']
            if not applications:
                raise Exception('Application %s not found!' % app_name)
            else:
                application = applications[0]
        else:
            raise Exception(r.text)
        
        app_id = application['id']

        pname = "".join([x.title() for x in metric_name.split('_')]) + 'Policy'
        policy_name = '%s_%s' % (app_name, pname)
        url = '%s/v2/alerts_policies.json' % (self.server_url)
        d = '?filter[name]=%s' % (policy_name)
        url = url + d
        r = requests.get(url, headers=self.request_headers_get())
        policy = None
        if r.status_code == 200:
            policies = json.loads(r.text)['policies']
            if not policies:
                m = {}
                p = {}
                p['name'] = policy_name
                p['incident_preference'] = 'PER_POLICY'
                m['policy'] = p
                url = '%s/v2/alerts_policies.json' % (self.server_url)
                d = json.dumps(m)
                r = requests.post(url, headers=self.request_headers_post(),data=d)
                if r.status_code == 201:
                    policy = json.loads(r.text)['policy']
                else:
                    raise Exception(r.text)
            else:
                policy = policies[0]
        else:
            raise Exception(r.text)
   
        url = '%s/v2/alerts_conditions.json' % (self.server_url)
        d = '?policy_id=%s' % (policy['id'])
        url = url + d
        r = requests.get(url, headers=self.request_headers_get())
        condition_name = 'ConditionResponseTime_%s' % (policy_name)
        condition = None
        if r.status_code == 200:
            conditions = json.loads(r.text)['conditions']
            if not conditions:
                m = {}
                c = {}
                c['name'] = condition_name
                c['enabled'] = 'true'
                e = [app_id]
                c['entities'] = e
                c['type'] = 'apm_app_metric'
                c['metric'] = metric_name
                c['condition_scope'] = "application"
                c['violation_close_timer'] = "24"
                t = [{"duration":"5","operator":operator,"priority":"critical","threshold":threshold,"time_function":"all"}]
                c['terms'] = t
                m['condition'] = c
                url = '%s/v2/alerts_conditions/policies/%s.json' % (self.server_url, policy['id'])
                d = json.dumps(m)
                r = requests.post(url, headers=self.request_headers_post(),data=d)
                if r.status_code == 201:
                    condition = json.loads(r.text)['condition']
                else:
                    raise Exception(r.text)
            else:
                m = {}
                condition = conditions[0]
                t = [{"duration":"5","operator":operator,"priority":"critical","threshold":threshold,"time_function":"all"}]
                condition['terms'] = t
                m['condition'] = condition
                url = '%s/v2/alerts_conditions/%s.json' % (self.server_url, condition['id'])
                d = json.dumps(m)
                r = requests.put(url, headers=self.request_headers_post(),data=d)
                if r.status_code == 200:
                    condition = json.loads(r.text)['condition']
                else:
                    raise Exception(r.text)
        else:
            raise Exception(r.text)

	url = '%s/v2/alerts_policy_channels.json?policy_id=%s&channel_ids=%s' % (self.server_url,policy['id'],self.channel_id)
	r = requests.put(url, headers=self.request_headers_post())
	if r.status_code == 200:
	    policy = json.loads(r.text)['policy']
	else:
	    raise Exception(r.text)

