from flask import Flask, render_template, request
import json
from aws_client import AWSClient
from cachet_client import CachetClient

app = Flask(__name__)

@app.route("/")
def main():
    return "It works!"

@app.route("/incidents/new",methods=['POST'])
def new_incident():
    j = request.get_json(force=True)
    print j

    component_name = j['component_name']
    component_group = j['group_name']
    i_name = j['name']
    i_msg = j['message']

    c = CachetClient()
    ret = {}

    try:
        i = c.report_incident(component_name=component_name, component_group_name=component_group, incident_name=i_name, message=i_msg)
        ret['status'] = 'success'
        ret['incident'] = i
    except Exception, e:
        ret['status'] = 'error'
        ret['error'] = '%s' % str(e)

    return json.dumps(ret)

@app.route("/incidents/fix",methods=['POST'])
def fix_incident():
    j = request.get_json(force=True)
    print j

    component_name = j['component_name']
    component_group = j['group_name']
    i_name = j['name']

    c = CachetClient()
    ret = {}

    try:
        i = c.fix_incident(component_name=component_name, component_group_name=component_group, incident_name=i_name)
        ret['status'] = 'success'
        ret['incident'] = i
    except Exception, e:
        ret['status'] = 'error'
        ret['error'] = '%s' % str(e)

    return json.dumps(ret)

@app.route("/components/new",methods=['POST'])
def new_component():
    j = request.get_json(force=True)
    print j

    component_name = j['component_name']
    component_group = None
    component_description = None
    
    if 'group_name' in j:
        component_group = j['group_name']

    if 'component_description' in j:
        component_description = j['component_description']

    c = CachetClient()
    ret = {}

    try:
        comp = c.find_or_create_component(component_name=component_name, component_description=component_description, component_group_name=component_group)
        ret['status'] = 'success'
        ret['component'] = comp
    except Exception, e:
        ret['status'] = 'error'
        ret['error'] = '%s' % str(e)

    return json.dumps(ret)


@app.route("/alarms/receive/newrelic",methods=['POST'])
def newrelic_alarm():
    j = request.get_json(force=True)
    print j

    app_name = j['targets'][0]['name']
    alarm_name = '%s - %s' % (app_name, j['condition_name'])
    new_state = j['current_state']
    new_state_reason = j['details']
    a_url = j['incident_url']
    
    i_name = alarm_name
    i_msg = "%s : %s - [NEWRELIC Incident](%s) " % (alarm_name, new_state_reason, a_url)

    component_name = app_name
    component_group = None

    if "_" in app_name:
        s = app_name.split('_')
        component_group = s[0]
        component_name = "_".join(s[1:])

    c = CachetClient()
    if new_state == 'open':
        c.report_incident(component_name=component_name, component_group_name=component_group, incident_name=i_name, message=i_msg)
    if new_state == 'closed':
        c.fix_incident(component_name=component_name, component_group_name=component_group, incident_name=i_name)

    return str(j)

@app.route("/alarms/receive/aws",methods=['POST'])
def aws_alarm():
    j = request.get_json(force=True)
    print j

    aws_msg = json.loads(j['Message'])
    dimens = aws_msg['Trigger']['Dimensions']
    is_ec2 = False
    is_rds = False
    resource_id = None
    for d in dimens:
        if d['name'] == 'DBInstanceIdentifier':
            resource_id = d['value']
            is_rds = True

        if d['name'] == 'InstanceId':
            resource_id = d['value']
            is_ec2 = True

    alarm_name = aws_msg['AlarmName']
    alarm_description = aws_msg['AlarmDescription']
    new_state_reason=aws_msg['NewStateReason']
    old_state = aws_msg['OldStateValue']
    new_state = aws_msg['NewStateValue']
    state_change_time = aws_msg['StateChangeTime']

    component_name = None
    component_group = None
    aws_client = AWSClient()
    r = None
    if is_ec2:
        r = aws_client.ec2_find_instance_by_id(resource_id)
    if is_rds:
        r = aws_client.rds_find_instances(db_instance_id=resource_id)[0]

    component_name = r[aws_client.tag_monitor_component_key]
    component_group = r[aws_client.tag_monitor_group_key]

    i_name = alarm_name
    i_msg = "%s %s : %s - %s (%s) [AWS-CloudWatch](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarm:alarmFilter=inAlarm)" % (new_state, alarm_name, new_state_reason, state_change_time,alarm_description)

    c = CachetClient()
    if new_state == 'ALARM':
        c.report_incident(component_name=component_name, component_group_name=component_group, incident_name=i_name, message=i_msg)
    if new_state == 'OK':
        c.fix_incident(component_name=component_name, component_group_name=component_group, incident_name=i_name)

    return str(j)
 
if __name__ == "__main__":
    app.run(host= '0.0.0.0', port=80)
