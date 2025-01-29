import boto3

client = boto3.client('redshift-serverless')

response = client.list_namespaces()
print(response)