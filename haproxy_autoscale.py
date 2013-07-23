from boto.ec2 import EC2Connection
from boto.ec2.securitygroup import SecurityGroup
from boto.ec2.autoscale import AutoScaleConnection
import boto
import urllib2
import logging
import iso8601
from datetime import datetime
from mako.template import Template

def get_self_instance_id():
    '''
    Get this instance's id.
    '''
    logging.debug('get_self_instance_id()')
    response = urllib2.urlopen('http://169.254.169.254/1.0/meta-data/instance-id')
    instance_id = response.read()
    return instance_id


def steal_elastic_ip(access_key=None, secret_key=None, ip=None, region='us-east-1'):
    '''
    Assign an elastic IP to this instance.
    '''
    logging.debug('steal_elastic_ip()')
    instance_id = get_self_instance_id()
    conn = EC2Connection(aws_access_key_id=access_key,
                         aws_secret_access_key=secret_key, region=boto.ec2.get_region(region))
    conn.associate_address(instance_id=instance_id, public_ip=ip)


def get_running_instances_in_security_group(access_key=None, secret_key=None, security_group=None, region='us-east-1'):
    '''
    Get all running instances. Only within a security group if specified.
    '''
    logging.debug('get_running_instances_in_security_group()')
    conn = EC2Connection(aws_access_key_id=access_key,
                         aws_secret_access_key=secret_key,region=boto.ec2.get_region(region))

    if security_group:
        sg = SecurityGroup(connection=conn, name=security_group)
        instances = [i for i in sg.instances() if i.state == 'running']
	print(instances)
        return instances

def get_running_instances_in_autoscaling_group(access_key=None, secret_key=None, autoscaling_group=None, region='us-east-1'):
    '''
    Get all running instances. Only within a security group if specified.
    '''
    logging.debug('get_running_instances_in_autoscaling_group()')
    conn = boto.ec2.autoscale.connect_to_region(region,aws_access_key_id=access_key,
                         aws_secret_access_key=secret_key)
    ec2_conn = boto.ec2.connect_to_region(region,aws_access_key_id=access_key,
                         aws_secret_access_key=secret_key)

    if autoscaling_group:
        asg = conn.get_all_groups(names=[autoscaling_group])[0]
	instance_ids = [i.instance_id for i in asg.instances if i.health_status=='Healthy' and i.lifecycle_state=='InService']
	reservations = ec2_conn.get_all_instances(instance_ids)
	for r in reservations:
		for i in r.instances:
			print("Status: ",i.state)
			print("DateTime.utcnow: ", datetime.utcnow())
			print("iso8601: ", iso8601.parse_date(i.launch_time).replace(tzinfo=None))
			print("Diff: ", (datetime.utcnow() - iso8601.parse_date(i.launch_time).replace(tzinfo=None)).seconds)
	instances = [i for r in reservations for i in r.instances if str(i.state)=='running' and ((datetime.utcnow() - iso8601.parse_date(i.launch_time).replace(tzinfo=None) ).seconds > 150)]
	print(instances)
	return instances


def file_contents(filename=None, content=None):
    '''
    Just return the contents of a file as a string or write if content
    is specified. Returns the contents of the filename either way.
    '''
    logging.debug('file_contents()')
    if content:
        f = open(filename, 'w')
        f.write(content)
        f.close()
    
    try:
        f = open(filename, 'r')
        text = f.read()
        f.close()
    except:
        text = None

    return text


def generate_haproxy_config(template=None, instances=None):
    '''
    Generate an haproxy configuration based on the template and instances list.
    '''
    return Template(filename=template).render(instances=instances)
