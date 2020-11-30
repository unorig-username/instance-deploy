import boto3
import os
import base64
from botocore.exceptions import ClientError
import logging
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

logger = logging.getLogger(__name__)
ec2 = boto3.resource("ec2")
uniq_hash = base64.b64encode(os.urandom(6)).decode("ascii")

# Load config.yaml
config = load(open("config.yaml", "r"), Loader=Loader)
# users = config['server']['users']
# volumes = config['server']['volumes']
server = config['server']
pem_path = "./creds/"

def create_pem(users):
    pem_names = []
    for user in users:
        try:
            # Normalize keypair and pem naming
            pem_name = f"{user['login']}_{uniq_hash}"
            logger.info(f"Pem file name: {pem_name}")
            pem_file = open(f"{pem_path}{pem_name}.pem","w")
            logger.info(f"Pem file opened")
            # Create KeyPair
            keypair = ec2.create_key_pair(KeyName=pem_name)
            logger.info(f"Pem Created Successfully")
            pem = str(keypair.key_material)
            pem_file.write(pem)
            logger.info(f"Pem File Closed")
        except ClientError:
            logger.exception(f"Issue creating Pem Key: {pem_name}")
            raise
        else:
            pem_names.append(pem_name)
    return pem_names

def setup_security_group(group_name="test_group", group_description="FR Coding Exercise."):
    try:
        default_vpc = list(ec2.vpcs.filter(
            Filters=[{'Name': 'isDefault', 'Values': ['true']}]))[0]
        logger.info(f"Got default VPC {default_vpc.id}.")
    except ClientError:
        logger.exception("Couldn't get VPCs.")
        raise
    except IndexError:
        logger.exception("No default VPC in the list.")
        raise
    try:
        group_name_uniq = f"{group_name}_{uniq_hash}"
        security_group = default_vpc.create_security_group(
            GroupName=group_name_uniq, Description=group_description)
        logger.info(
            f"Created security group {group_name_uniq} in VPC {default_vpc.id}.")
    except ClientError:
        logger.exception(f"Couldn't create security group {group_name_uniq}.")
        raise
    try:
        ip_permissions = [{
            # SSH ingress open to anyone (DEFINITELY NOT PROD READY. STILL WILL NEED PEM KEY. JUST FOR PROOF OF CONCEPT!)
            'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }]
        security_group.authorize_ingress(IpPermissions=ip_permissions)
        logger.info(f"Set inbound rules for {security_group.id}||{group_name_uniq} to allow all inbound for SSH.")
    except ClientError:
        logger.exception(f"Couldnt authorize inbound rules for {group_name_uniq}.")
        raise
    else:
        return group_name_uniq



def normalize_volumes(volumes):
    ### Short on Time Will need to revist ###
    normalized_vols = []
    for each in volumes:
        volume = {
            "DeviceName": f"{each['type']}"
        }
        

def image(server):
    # Use AWS Systems Manager to find the latest AMI with required params #
    ssm = boto3.client('ssm')
    ami_params = ssm.get_parameters_by_path(
        Path='/aws/service/ami-amazon-linux-latest')
    amzn2_amis = [ap for ap in ami_params['Parameters'] if
                  all(query in ap['Name'] for query
                      in (server['ami_type'], server['virtualization_type'], server['architecture'], "gp2"))]
    if len(amzn2_amis) > 0:
        ami_image_id = amzn2_amis[0]['Value']
        logger.info(f"Found an AMI matching {server['ami_type']}, {server['architecture']}, and gp2.")
    elif len(ami_params) > 0:
        ami_image_id = ami_params['Parameters'][0]['Value']
        logger.info("Found an Amazon Machine Image (AMI) to use for the demo.")
    else:
        logger.exception("Couldn't locate any AMIs in the default path specified.")
        raise
    return ami_image_id

def spin_up(server):
    ### New Instance Creation ###
    try:
        image_id = image(server)
        key_name = create_pem(server['users'])[0]
        sg = setup_security_group()
        instance_params = {
            "ImageId": image_id, 
            "InstanceType": server['instance_type'], 
            "KeyName": key_name, 
            "SecurityGroups": [
                sg
            ], 
            "MaxCount": server['max_count'], 
            "MinCount": server['min_count']
        }
        instance = ec2.create_instances(**instance_params)
        instance[0].wait_until_running()
        instance[0].reload()
        public_ip = instance[0].public_ip_address
    except ClientError:
        logging.exception(f"Couldn't create the instances with the following parameters: {instance_params}")
        raise
    else:
        return public_ip, key_name


if __name__ == '__main__':
    instance_info = spin_up(server)
    ip = instance_info[0]
    pem = f"{pem_path}{instance_info[1]}.pem"
    os.chmod(pem, 0o600)
    ssh_cmd = f'####  ssh -i {pem} ec2-user@{ip}  ####'
    header_footer = '#' * len(ssh_cmd)
    filler = f'####{" " * (len(ssh_cmd) - 8)}####'

    print(f"Please use the following to connect to your EC2 instance {ip} :")
    print(header_footer)
    print(filler)
    print(ssh_cmd)
    print(filler)
    print(header_footer)
