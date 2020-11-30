# Deployment Tech Assessment
The purpose of this repo/application is to develop an automation program that takes a YAML configuration file as input and deploys a Linux AWS EC2 instance with two volumes and two users.

## Pre-Req
- An AWS Account
- An Access Key/Secret that has been added to `~/.aws/credentials` and has Admin priveleges (for the proof of concept). Will need to lockdown perms after development.
- Python3 (might want to make sure it's in your user's path)
- PyYaml `pip3 install pyyaml`
- Boto3 `pip3 install boto3`

## Launch Instance and Remotely Access.
1. After the pre-reqs are met above, you'll want to clone this repo locally (or wherever you want to run the script).
2. Open up a shell terminal in the root of the `deployment` repo and proceed to execute the following: `python3 deploy.py`
3. After successfully completing, you will have two new PEM keys in the `./creds/` directory, and you will see a command that you can run to remotely ssh into the instance created.
4. When executing the ssh command provided, it will prompt to make sure you would like to connect to the EC2 instance. Please type `yes` and hit enter/return
5. ???
6. Profit
