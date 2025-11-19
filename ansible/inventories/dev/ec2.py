#!/usr/bin/env python3
import boto3
import json
import os

def generate_inventory(instances):
    inventory = {"_meta": {"hostvars": {}}}
    inventory["ec2_hosts"] = {"hosts": [], "vars": {}}

    for reservation in instances:
        for instance in reservation["Instances"]:
            if instance.get("State", {}).get("Name") != "running":
                continue
            ip = instance.get("PublicIpAddress")
            if not ip:
                continue

            inventory["ec2_hosts"]["hosts"].append(ip)
            inventory["_meta"]["hostvars"][ip] = {
                "ansible_connection": "ssh",
                "ansible_user": "ubuntu",
                "ansible_ssh_private_key_file": "/var/lib/jenkins/.ssh/legacy-java-app-key"
            }

    return inventory

def main():
    region = os.environ.get("AWS_REGION")
    ec2 = boto3.client("ec2", region_name=region)
    response = ec2.describe_instances(
    Filters=[
        {"Name": "tag:Environment", "Values": ["dev"]}, 
        {"Name": "tag:app", "Values": ["legacy-java-app"]} 
    ]
)

    inventory = generate_inventory(response["Reservations"])
    print(json.dumps(inventory, indent=4))

if __name__ == "__main__":
    main()






