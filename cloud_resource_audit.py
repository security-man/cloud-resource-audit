import boto3
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
import os

def GetAzureResourceGroups():
    # Acquire a credential object.
    credential = DefaultAzureCredential()
    # Retrieve subscription ID from environment variable.
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    # Obtain the management object for resources.
    resource_client = ResourceManagementClient(credential, subscription_id)
    # Retrieve the list of resource groups
    group_list = resource_client.resource_groups.list()
    resource_groups = []
    for group in list(group_list):
        resource_groups.append(group.name)
    return resource_groups

def GetAzureResources(resource_groups):
    print("Getting Azure resource list")
    # Acquire a credential object.
    credential = DefaultAzureCredential()
    # Retrieve subscription ID from environment variable.
    subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]
    # Obtain the management object for resources.
    resource_client = ResourceManagementClient(credential, subscription_id)
    # Retrieve the list of resource groups
    resource_group_upper = [x.upper() for x in resource_groups]
    resource_list = resource_client.resources.list()
    resource_groups_count = [0] * len(resource_groups)
    dict = []
    for resource in resource_list:
        dict.append(resource.as_dict())
    for item in dict:
        resource_id = item['id']
        string_list = resource_id.split("/")
        resource_group = (string_list[4]).upper()
        resource_groups_count[resource_group_upper.index(resource_group)] += 1
    return resource_groups_count

def WriteAzureSummaryFile(resource_groups,resource_counts):
    print("Writing azure_summary.csv")
    total_resource_count = sum(resource_counts)
    file = open('azure_summary.csv','w')
    file.write('ResourceGroup,TotalResources,FractionOfTotal\n')
    for resource_group in resource_groups:
        fractional_count = resource_counts[resource_groups.index(resource_group)] / total_resource_count
        file.write(resource_group + ',' + str(resource_counts[resource_groups.index(resource_group)]) + ',' + str(fractional_count) + '\n')
    file.close()

def GetAwsAccounts():
    # establish client with root account (default profile)
    session = boto3.Session(profile_name="default")
    org = session.client('organizations')

    # paginate through all org accounts
    paginator = org.get_paginator('list_accounts')
    page_iterator = paginator.paginate()

    # get accounts ids for active accounts
    account_ids = []
    account_names = []
    account_name_sanitised = ""
    for page in page_iterator:
        for account in page['Accounts']:
            if account['Status'] == 'ACTIVE':
                account_ids += {account['Id']}
                account_name_sanitised = account['Name']
                account_name_sanitised = ''.join(account_name_sanitised.split())
                account_names += {account_name_sanitised}
    
    return account_ids, account_names
    
def GetAwsAccountResources(account_id):
    # initiates sessions / clients per aws profile (account combined with security audit role)
    if account_id == os.environ["AWS_ROOT_ACCOUNT_ID"]:
        profile = "default"
    else:
        profile = account_id + "-RO"
    session = boto3.Session(profile_name=profile)
    config_client = session.client('config', region_name="eu-west-2")
    resource_counts = config_client.get_discovered_resource_counts()
    total_resources = resource_counts['totalDiscoveredResources']
    return total_resources

def WriteAwsSummaryFile(account_ids,account_names):
    temporary_list = []
    total_resource_count = 0
    file = open('aws_summary.csv','w')
    file.write('AccountId,AccountName,TotalResources,FractionOfTotal\n')
    for account_id in account_ids:
        print("Request to AWS account ID " + account_id)
        temporary_list.append([account_id,account_names[account_ids.index(account_id)],GetAwsAccountResources(account_id)])
        total_resource_count += temporary_list[account_ids.index(account_id)][2]
    fractional_count = 0
    print("Writing aws_summary.csv")
    for account_id in account_ids:
        fractional_count = temporary_list[account_ids.index(account_id)][2] / total_resource_count
        file.write(temporary_list[account_ids.index(account_id)][0]+','+temporary_list[account_ids.index(account_id)][1]+','+str(temporary_list[account_ids.index(account_id)][2])+','+str(fractional_count)+'\n')
    file.close()

# Do Azure audit
resource_groups = GetAzureResourceGroups()
resource_counts = GetAzureResources(resource_groups)
WriteAzureSummaryFile(resource_groups,resource_counts)

# Do AWS audit
account_ids, account_names = GetAwsAccounts()
WriteAwsSummaryFile(account_ids,account_names)