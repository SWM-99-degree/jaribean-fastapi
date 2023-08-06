import sys
import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

load_dotenv()

def send_messages(msgBody):
    
    SQS_URL = os.getenv("SQS_URL")
    aws_access_key = os.getenv("AWS_ID")
    aws_secret_key = os.getenv("AWS_PASS")
    sqs_client = boto3.client('sqs', region_name='ap-northeast-2', 
                              aws_access_key_id=aws_access_key,
                            aws_secret_access_key=aws_secret_key,)
    try:
        msg = sqs_client.send_message(QueueUrl=SQS_URL,
                                      MessageBody=msgBody, MessageGroupId="matching")
    except ClientError as e:
        return None
    return 1
    