#!/usr/bin/python

import boto3
import os

class AWSClient():

    def __init__(self, topic=None, tag_monitor_group_key=None, tag_monitor_component_key=None, prefix_alarm="_DrHibbert"):
        self.topic_alarm = os.getenv('DRHIBBERT_AWS_TOPICALARM',topic)
        self.tag_monitor_group_key = os.getenv('DRHIBBERT_AWS_TAG_MONITOR_GROUP_KEY',tag_monitor_group_key)
        self.tag_monitor_component_key = os.getenv('DRHIBBERT_AWS_TAG_MONITOR_COMPONENT_KEY',tag_monitor_component_key)
        self.prefix_alarm = os.getenv('DRHIBBERT_AWS_PREFIX_ALARM',prefix_alarm)

    def ec2_find_instance_by_id(self,instance_id):
        ec2 = boto3.resource('ec2')
        ec2_instance = ec2.Instance(instance_id)
        attrs = {}
        attrs['Id'] = instance_id
        attrs['_AWS_Tags'] = ec2_instance.tags
        attrs[self.tag_monitor_group_key] = None
        attrs[self.tag_monitor_component_key] = None
        for tags in ec2_instance.tags:
            if tags["Key"] == self.tag_monitor_group_key:
                attrs[self.tag_monitor_group_key] = tags["Value"]
            if tags["Key"] == self.tag_monitor_component_key:
                attrs[self.tag_monitor_component_key] = tags["Value"]
            if tags["Key"] == 'Name':
                attrs['Name'] = tags["Value"]
        return attrs

    def rds_find_instances(self, db_instance_id=None, db_arn=None):
        ret = []
        rds_client = boto3.client('rds')
        if db_instance_id:
            rds_instances = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_id)
        else:
            if db_arn:
                rds_instances = rds_client.describe_db_instances(
                                           Filters=[
                                                     {
                                                         'Name': 'db-instance-id',
                                                         'Values': [db_arn]
                                                     }
                                                   ],
                                           )
            else:
                rds_instances = rds_client.describe_db_instances()

        for r in rds_instances['DBInstances']:
            attrs = {}
            attrs['Id'] = r['DBInstanceIdentifier']
            attrs['Arn'] = r['DBInstanceArn']
            attrs[self.tag_monitor_group_key] = None
            attrs[self.tag_monitor_component_key] = None
            tags = rds_client.list_tags_for_resource(ResourceName=r['DBInstanceArn'])['TagList']
            attrs['_AWS_Tags'] = tags
            for t in tags:
                if t["Key"] == self.tag_monitor_group_key:
                    attrs[self.tag_monitor_group_key] = t["Value"]
                if t["Key"] == self.tag_monitor_component_key:
                    attrs[self.tag_monitor_component_key] = t["Value"]
                if t["Key"] == 'Name':
                    attrs['Name'] = t["Value"]
            ret.append(attrs)
        return ret
     

    def ec2_list_instances_by_tag_value(self, tagkey, tagvalue):
        ec2_client = boto3.client('ec2')
        response = ec2_client.describe_instances(Filters=[{'Name': 'tag:'+tagkey, 'Values': [tagvalue]}])
        instancelist = []
        for reservation in (response["Reservations"]):
            for instance in reservation["Instances"]:
                instancelist.append(instance["InstanceId"])
        return instancelist

    def ec2_add_tags(self, resources_id, tags):
        ec2_client = boto3.client('ec2')
        aws_tags = []
        for t in tags:
            aws_tags.append({'Key':t,'Value':tags[t]})
        ec2_client.create_tags(Resources=resources_id,Tags=aws_tags)

    def rds_add_tags(self, resource_name, tags):
        rds_client = boto3.client('rds')
        aws_tags = []
        for t in tags:
            aws_tags.append({'Key':t,'Value':tags[t]})
        rds_client.add_tags_to_resource(ResourceName=resource_name,Tags=aws_tags)

    def ec2_delete_tags(self, resources_id, tags):
        ec2_client = boto3.client('ec2')
        aws_tags = []
        for t in tags:
            aws_tags.append({'Key':t,'Value':tags[t]})
        ec2_client.delete_tags(Resources=resources_id,Tags=aws_tags)

    def rds_delete_tags(self, resource_name, tags):
        rds_client = boto3.client('rds')
        rds_client.remove_tags_from_resource(ResourceName=resource_name,TagKeys=tags)

    def ec2_set_monitor_group(self, resources_id, monitor_group):
        t = {self.tag_monitor_group_key:monitor_group}
        c.ec2_add_tags(resources_id, t)

    def ec2_set_monitor_component(self, resources_id, monitor_component, monitor_group=None):
        t = {self.tag_monitor_component_key:monitor_component}
        if monitor_group:
            t[self.tag_monitor_group_key] = monitor_group
        c.ec2_add_tags(resources_id, t)

    def rds_set_monitor_component(self, resource_name, monitor_component, monitor_group=None):
        t = {self.tag_monitor_component_key:monitor_component}
        if monitor_group:
            t[self.tag_monitor_group_key] = monitor_group
        c.rds_add_tags(resource_name, t)

    def rds_set_monitor_group(self, resource_name, monitor_group):
        t = {self.tag_monitor_group_key:monitor_group}
        c.rds_add_tags(resource_name, t)

    def ec2_create_alarm(self, resources_id, metric_namespace, metric_name, operator, threshold, unit):
        cloudwatch = boto3.client('cloudwatch')

        for resource_id in resources_id:
            alarm_name = '%s_Monitor_EC2_%s_%s' % (self.prefix_alarm, metric_name, resource_id)

            cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator=operator,
                EvaluationPeriods=1,
                MetricName=metric_name,
                Namespace=metric_namespace,
                Period=300,
                Statistic='Average',
                Threshold=threshold,
                ActionsEnabled=True,
                AlarmActions=[self.topic_alarm],
                OKActions=[self.topic_alarm],
                AlarmDescription='Alarm when %s %s %s' % (metric_name,operator,threshold),
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': resource_id
                    },
                ],
                Unit=unit
            )

    def ec2_create_alarm_cpu(self, resources_id, operator='GreaterThanThreshold', threshold=85.0):
        self.ec2_create_alarm(resources_id,'AWS/EC2','CPUUtilization',operator,threshold, unit='Percent')

    def ec2_create_alarm_mem(self, resources_id, operator='GreaterThanThreshold', threshold=85.0):
        self.ec2_create_alarm(resources_id,'System/Linux','MemoryUtilization',operator,threshold,unit='Percent')

    def ec2_create_alarm_disk(self, resources_id, operator='GreaterThanThreshold', threshold=85.0):
        self.ec2_create_alarm(resources_id,'System/Linux','DiskSpaceUtilization',operator,threshold,unit='Percent')

    def rds_create_alarm(self, resources_id, metric_namespace, metric_name, operator, threshold, unit):
        cloudwatch = boto3.client('cloudwatch')

        for resource_id in resources_id:
            alarm_name = '%s_Monitor_RDS_%s_%s' % (self.prefix_alarm, metric_name, resource_id)

            cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator=operator,
                EvaluationPeriods=1,
                MetricName=metric_name,
                Namespace=metric_namespace,
                Period=300,
                Statistic='Average',
                Threshold=threshold,
                ActionsEnabled=True,
                AlarmActions=[self.topic_alarm],
                OKActions=[self.topic_alarm],
                AlarmDescription='Alarm when %s %s %s' % (metric_name,operator,threshold),
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': resource_id
                    },
                ],
                Unit=unit
            )

    def rds_create_alarm_cpu(self, resources_id, operator='GreaterThanThreshold', threshold=85.0):
        self.rds_create_alarm(resources_id, 'AWS/RDS','CPUUtilization', operator,threshold,unit='Percent')

    def rds_create_alarm_mem(self, resources_id, operator='LessThanThreshold', threshold=250000000):
        self.rds_create_alarm(resources_id, 'AWS/RDS', 'FreeableMemory', operator,threshold,unit='Bytes')

    def rds_create_alarm_disk(self, resources_id, operator='LessThanThreshold', threshold=3000000000):
        self.rds_create_alarm(resources_id, 'AWS/RDS', 'FreeStorageSpace', operator,threshold,unit='Bytes')

    def rds_create_alarm_disk_queue(self, resources_id, operator='GreaterThanThreshold', threshold=5):
        self.rds_create_alarm(resources_id, 'AWS/RDS', 'DiskQueueDepth', operator,threshold,unit='Count')

