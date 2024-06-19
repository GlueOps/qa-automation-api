import boto3
import json

def assume_role(account_alias, role_name="OrganizationAccountAccessRole"):
    client = boto3.client('organizations')
    
    # List all accounts in the organization
    paginator = client.get_paginator('list_accounts')
    page_iterator = paginator.paginate()
    
    # Find the account with the given alias
    account_id = None
    for page in page_iterator:
        for account in page['Accounts']:
            if account['Name'].lower() == account_alias.lower():
                account_id = account['Id']
                break
        if account_id:
            break
    

    
    if not account_id:
        raise ValueError(f"Account with alias '{account_alias}' not found.")
    
    sts_client = boto3.client('sts')
    
    assumed_role = sts_client.assume_role(
        RoleArn=f'arn:aws:iam::{account_id}:role/{role_name}',
        RoleSessionName='AssumeRoleSession'
    )
    
    return assumed_role['Credentials'], account_id

def create_iam_user(credentials, user_name):
    iam_client = boto3.client(
        'iam',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    
    # Create IAM user
    iam_client.create_user(UserName=user_name)
    
    # Attach AdministratorAccess policy to the user
    iam_client.attach_user_policy(
        UserName=user_name,
        PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
    )
    
    # Create access key for the user
    access_key = iam_client.create_access_key(UserName=user_name)
    
    return access_key['AccessKey']

def create_role_with_admin_access(credentials, role_name, account_id):
    iam_client = boto3.client(
        'iam',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    
    assume_role_policy_document = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{account_id}:root"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    })
    
    # Create role
    iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=assume_role_policy_document
    )
    
    # Attach AdministratorAccess policy to the role
    iam_client.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
    )


def account_setup(account_alias, aws_role_name_to_create):
    credentials, account_id = assume_role(account_alias)
    captain_user_details = create_iam_user(credentials, "glueops-captain")
    create_role_with_admin_access(credentials, aws_role_name_to_create, account_id)
    env_file_for_aws = f"""
### AWS Account Name: {account_alias}
export AWS_ACCESS_KEY_ID="{credentials['AccessKeyId']}"
export AWS_SECRET_ACCESS_KEY="{credentials['SecretAccessKey']}"
export AWS_DEFAULT_REGION=us-west-2
#aws eks update-kubeconfig --region us-west-2 --name captain-cluster --role-arn arn:aws:iam::{account_id}:role/{aws_role_name_to_create}  

"""
    return env_file_for_aws