from __future__ import print_function
import json
import boto3
import urllib3
import json
import os
import time
SUCCESS = "SUCCESS"
FAILED = "FAILED"
http = urllib3.PoolManager()
redshift_data = boto3.client('redshift-data')
def describestatement(statement_id):
    print(f'Batch statement ID: {statement_id}')
    time.sleep(10)
    while True:
        # Describe the batch statement
        describe_response = redshift_data.describe_statement(Id=statement_id)
        print(describe_response)
        status = describe_response['Status']
        if status == 'FINISHED':
            print('Batch statement executed successfully')
            break
        elif status in ['FAILED', 'ABORTED']:
            print(f'Batch statement failed with status: {status}')
            break
        else:
            print(f'Batch statement status: {status}')
            time.sleep(5)
    return status
def managedatashareconsumer(requestType, datashareName, workgroupName,databaseNameConnection,databaseNameFromDatashare,secretArn,producerAccount,producerNamespaceIdentifier):
    sqls = []
    status = ""
    if requestType == 'Create' or requestType == 'Update' :
        sql="CREATE DATABASE " + databaseNameFromDatashare + " FROM DATASHARE " + datashareName +  " OF ACCOUNT " + producerAccount + " NAMESPACE " + producerNamespaceIdentifier
        response = redshift_data.execute_statement(
            WorkgroupName=workgroupName,
            Database=databaseNameConnection,
            SecretArn=secretArn,
            Sql=sql
        )
        status = describestatement( response['Id'])
    if requestType == 'Delete' :
        sql="DROP DATABASE " + databaseNameFromDatashare
        response = redshift_data.execute_statement(
            WorkgroupName=workgroupName,
            Database=databaseNameConnection,
            SecretArn=secretArn,
            Sql=sql
        )
        status = describestatement( response['Id'])
    status = describestatement( response['Id'])

    if status == "FINISHED" :
        return SUCCESS
    else :
        return FAILED
def send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False, reason=None):
    responseUrl = event['ResponseURL']
    print(responseUrl)
    responseBody = {
        'Status' : responseStatus,
        'Reason' : reason or "See the details in CloudWatch Log Stream: {}.format(context.log_stream_name)",
        'PhysicalResourceId' : physicalResourceId or context.log_stream_name,
        'StackId' : event['StackId'],
        'RequestId' : event['RequestId'],
        'LogicalResourceId' : event['LogicalResourceId'],
        'NoEcho' : noEcho,
        'Data' : responseData
    }
    json_responseBody = json.dumps(responseBody)
    print("Response body:")
    print(json_responseBody)
    headers = {
        'content-type' : '',
        'content-length' : str(len(json_responseBody))
    }
    try:
        response = http.request('PUT', responseUrl, headers=headers, body=json_responseBody)
        print("Status code:", response.status)
    except Exception as e:
        print("send(..) failed executing http.request(..):", e)
def lambda_handler(event, context):
    print('Event:', json.dumps(event))
    try: 
        datashareName = os.environ.get('DATASHARE_NAME')#'bbc-poc-datashare-writable-vincent'#
        workGroupName = os.environ.get('WORKGROUP_NAME')#'bbc-poc-debug-cf-vincent-preview'#
        databaseNameConnection = os.environ.get('DATABASE_NAME_CONNECTION')#'dev'
        databaseNameFromDatashare = os.environ.get('DATABASE_NAME_FROM_DATASHARE')#'dev'
        secretArn = os.environ.get('SECRET_ARN')#'arn:aws:secretsmanager:eu-west-1:205930640479:secret:redshift!bbc-poc-debug-cf-vincent-preview-awsuser-ufKzNP'#
        producerAccount = os.environ.get('PRODUCER_ACCOUNT')#'75b82897-833c-43d2-b17d-c369efc5d0b7'#
        producerNamespaceIdentifier = os.environ.get('PRODUCER_NAMESPACE_IDENTIFIER')#'75b82897-833c-43d2-b17d-c369efc5d0b7'#
        if event['RequestType'] == 'Create':
            print('Performing post-deployment create action')
        if event['RequestType'] == 'Update':
            print('Performing post-deployment update action')
        if event['RequestType'] == 'Delete':
            print('Performing post-deployment delete action') 
        cfstatus=managedatashareconsumer(event['RequestType'], datashareName, workGroupName,databaseNameConnection,databaseNameFromDatashare, secretArn,producerAccount,producerNamespaceIdentifier)
        if cfstatus == SUCCESS:
            send(event, context, SUCCESS, {"Message": "DataShare configuration successfully done."})
        else :
            send(event, context, FAILED, {"Message": "DataShare configuration failed."})
    except Exception as e:
        print("Exception: ", str(e)) 
        send(event, context, FAILED, {"Message": "Action cannot becompleted."})
    return {
        'Status': 'SUCCESS',
        'Reason': 'Action completed',
    }
