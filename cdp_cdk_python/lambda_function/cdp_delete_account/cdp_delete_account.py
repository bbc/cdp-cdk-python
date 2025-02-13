import json
import uuid

import boto3
import requests
import os
from botocore.exceptions import ClientError
import base64
from datetime import datetime

#Example SNS consumer lambda function to consume delete account requests
#and forward them to a 3rd party api e.g. mParticle
#Very basic example and needs fleshing out / testing / to be completed

def lambda_handler(event, context):
    sqs_client = boto3.client('sqs')
    queue_url = os.getenv("queue_url")
    dead_letter_queue_url = os.getenv("dead_letter_queue_url")
    external_endpoint = os.getenv("external_endpoint_post_url")
    mParticle_api_secret_name  = os.getenv("mParticle_api_secret_name")
    # api_key = os.getenv("api_key")
    # api_secret = os.getenv("api_secret")
    callback_url = os.getenv("callback_url")

    # Generate the authorization token
    client = boto3.client("secretsmanager")

    try:
        # ✅ Get the secret value
        response = client.get_secret_value(SecretId=mParticle_api_secret_name)
        api_key = json.loads(response["mParticleAPIKey"])
        api_secret = json.loads(response["mParticleAPISecret"])
        raw_token = f"{api_key}:{api_secret}"
        encoded_token = base64.b64encode(raw_token.encode("utf-8")).decode("utf-8")
        authorization_token = f"Basic {encoded_token}"
        print(authorization_token)

    except Exception as e:
        return f"Error retrieving secret: {str(e)}"
    

    # Fail fast if no messages
    try:
        attributes = sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        message_count = int(attributes.get('Attributes', {}).get('ApproximateNumberOfMessages', 0))

        if message_count == 0:
            print("No messages in the queue. Exiting.")
            return {
                'statusCode': 200,
                'body': json.dumps('No messages to process')
            }
    except Exception as e:
        print(f"Error checking queue message size: {e}. Continuing anyway")

    # There are messages, process
    try:
        # Receive messages from SQS
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20, # Long polling
            VisibilityTimeout = 80 # Dont show message again to re-try for x seconds
        )

        messages = response.get('Messages', [])

        for message in messages:
            receipt_handle = message['ReceiptHandle']
            try:
                sns_message = json.loads(message['Body'])
                process_message(sns_message, external_endpoint, authorization_token, callback_url)

            except Exception as e:
                print(f"Error processing message: {e} - moving to dlq")
                # Move the message to the Dead Letter Queue if error
                try:
                    sqs_client.send_message(
                        QueueUrl=dead_letter_queue_url,
                        MessageBody=json.dumps(message)
                    )

                except ClientError as dlq_error:
                    print(f"Failed to send message to Dead Letter Queue: {dlq_error}")

            try:
                # Delete the message from the queue after processing
                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
            except Exception as e:
                print(f"Error deleting message: {e}")

    except ClientError as e:
        print(f"Error receiving messages: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps('Messages processed successfully')
    }

def process_message(sns_message, external_endpoint, authorization_token, callback_url):
    try:
        #TODO Finish this. Base request unfinished. What info do we have from the message?
        #TODO How can we translate this info to a mParticle deletion request?
        #TODO May have to hook into BBC account api to get some clean details back to mParticle
        payload = {
            "regulation": "gdpr",
            "subject_request_id": str(uuid.uuid4()),  # Generate a unique UUID v4
            "subject_request_type": "erasure",
            "submitted_time": datetime.utcnow().isoformat() + "Z",  # Current time in ISO 8601 format
            "subject_identities": {
                "email": {
                    "value": sns_message.get('email', 'null'),
                    "encoding": "raw"
                },
                "ios_advertising_id": {
                    "value": sns_message.get('ios_id', 'null'),
                    "encoding": "raw"
                }
            },
            "api_version": "3.0",
            "status_callback_urls": [
                callback_url
            ],
            "group_id": "my-group",
            "extensions": {
                "opendsr.mparticle.com": {
                    "skip_waiting_period": False,
                    "subject_identities": {
                        "other6": {
                            "value": "EA7583CD-A667-48BC-B806-42ECB2B48606",
                            "encoding": "raw"
                        }
                    }
                }
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {authorization_token}"
        }

        response = requests.post(external_endpoint, json=payload, headers=headers)
        response.raise_for_status() #decodes the response body and throws an exception for HTTP codes 400-599
        print(f"External API response: {response.text}")

    except json.JSONDecodeError as e:
        print(f"Error decoding SNS message: {e}")
    except requests.RequestException as e:
        print(f"Error making REST call: {e}")
