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
def managedatashare(requestType, datashareName, clusterIdentifier,databaseName,SchemaNameReadOnly,SchemaNameToWrite,secretArn,tablesGrantSelect,tablesGrantInsert,tablesGrantUpdate,tablesGrantDelete,consumerAccount):
    sqls = []
    if requestType == 'Create' :
        sqls.append(f'CREATE DATASHARE "{datashareName}";');
        for readSchemaName in SchemaNameReadOnly.split(','):
            sqls.append(f'ALTER DATASHARE "{datashareName}" ADD SCHEMA {readSchemaName} ;')
            sqls.append(f'ALTER DATASHARE "{datashareName}" ADD ALL TABLES IN SCHEMA {readSchemaName} ;')
            sqls.append(f'ALTER DATASHARE "{datashareName}" SET INCLUDENEW = TRUE FOR SCHEMA {readSchemaName} ;')
        sqls.append(f'ALTER DATASHARE "{datashareName}" ADD SCHEMA {SchemaNameToWrite};')
        if tablesGrantSelect:
            for table in  tablesGrantSelect.split(','):
                sqls.append(f'GRANT SELECT ON TABLE {SchemaNameToWrite}.{table} TO DATASHARE "{datashareName}";')
        if tablesGrantSelect:
            for table in  tablesGrantInsert.split(','):
                sqls.append(f'GRANT INSERT ON TABLE {SchemaNameToWrite}.{table} TO DATASHARE  "{datashareName}";')
        if tablesGrantSelect:
            for table in  tablesGrantUpdate.split(','):
                sqls.append(f'GRANT UPDATE ON TABLE {SchemaNameToWrite}.{table} TO DATASHARE  "{datashareName}";')
        if tablesGrantSelect:
            for table in  tablesGrantDelete.split(','):
                sqls.append(f'GRANT DELETE ON TABLE {SchemaNameToWrite}.{table} TO DATASHARE  "{datashareName}";')
    if requestType == 'Delete' :
        sqls.append(f'DROP DATASHARE "{datashareName}";');
    print(sqls)
    response = redshift_data.batch_execute_statement(
        ClusterIdentifier=clusterIdentifier,
        Database=databaseName,
        SecretArn=secretArn,
        Sqls=sqls
    ) 
    status = describestatement( response['Id'])
    if  status == "FINISHED" and requestType == 'Create':
        response = redshift_data.execute_statement(
            ClusterIdentifier=clusterIdentifier,
            Database=databaseName,
            SecretArn=secretArn,
            Sql="GRANT USAGE ON DATASHARE " + datashareName + " TO ACCOUNT '" + consumerAccount + "';"
        ) 
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
        'Reason' : reason or "See the details in CloudWatch Log Stream: {}".format(context.log_stream_name),
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
        datashareName = os.environ.get('DATASHARE_NAME')
        clusterName = os.environ.get('CLUSTER_NAME')
        databaseName = os.environ.get('DATABASE_NAME')#'dev'
        SchemaNameToWrite = os.environ.get('SCHEMA_NAME_WRITE')#'public'#
        SchemaNameReadOnly = os.environ.get('SCHEMA_NAME_READ')
        secretArn = os.environ.get('SECRET_ARN')
        consumerAccount = os.environ.get('CONSUMER_ACCOUNT')
        tablesGrantSelect =  os.environ.get('TABLES_GRANT_SELECT')#'customer,lineitem,nation'#
        tablesGrantInsert =  os.environ.get('TABLES_GRANT_INSERT')#'customer,lineitem,nation'#
        tablesGrantUpdate =  os.environ.get('TABLES_GRANT_UPDATE')#'customer,lineitem,nation'#
        tablesGrantDelete =  os.environ.get('TABLES_GRANT_DELETE')#'customer,lineitem,nation'#
        if event['RequestType'] == 'Create':
            print('Performing post-deployment create action')
        if event['RequestType'] == 'Update':
            print('Performing post-deployment update action')
        if event['RequestType'] == 'Delete':
            print('Performing post-deployment delete action') 
        cfstatus=managedatashare(event['RequestType'], datashareName, clusterName,databaseName,SchemaNameReadOnly,SchemaNameToWrite,secretArn,tablesGrantSelect,tablesGrantInsert,tablesGrantUpdate,tablesGrantDelete,consumerAccount)
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