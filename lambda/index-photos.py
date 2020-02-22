from __future__ import print_function
import json
import base64
import boto3
import math, random
import uuid
import time
from requests_aws4auth import AWS4Auth
import requests

region = 'us-east-1'  # e.g. us-east-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

host = 'https://vpc-phototest-cf3yzd2ygbbho7cea7dy57wyma.us-east-1.es.amazonaws.com'  # the Amazon ES domain, with https://
index = 'photos'
type = 'Photo'
url = host + '/' + index + '/' + type + '/'
searchUrl =  host + '/' + index + '/_search?q='
headers = {"Content-Type": "application/json"}


def detect_labels(photo, bucket):
    print(photo)
    print(bucket)
    client=boto3.client('rekognition','us-east-1')
    
    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
                                    MaxLabels=10)
    print('Detected labels for ' + photo)
    print()
    label_string = []
    for label in response['Labels']:
        label_string.append(label['Name'])
    document = {
        'objectKey': photo,
        'bucket': bucket,
        'createdTimestamp': time.time(),
        'labels': label_string
    }
    print("string = ")
    print(label_string)
    print(" ")
    r = requests.post(url, auth=awsauth, json=document, headers=headers)
    response2 = requests.get(searchUrl+'Mountain',headers=headers)
    print(response2.text)
    return len(response['Labels'])

def lambda_handler(event, context):
    print(event)
    #print(event['s3'])
    photo_name = event['Records'][0]['s3']['object']['key']
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    detect_labels(photo_name, bucket_name)
