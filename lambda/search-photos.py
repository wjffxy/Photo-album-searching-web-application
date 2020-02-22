import json
import boto3
import os
import sys
import uuid
import time
import requests

ES_HOST = 'https://vpc-phototest-cf3yzd2ygbbho7cea7dy57wyma.us-east-1.es.amazonaws.com'
REGION = 'us-east-1'


def get_url(es_index, es_type, keyword):
    url = ES_HOST + '/' + es_index + '/' + es_type + '/_search?q=' + keyword.lower()
    return url

def lambda_handler(event, context):
	# recieve from API Gateway
	print("EVENT --- {}".format(json.dumps(event)))
	headers = { "Content-Type": "application/json" }
	lex = boto3.client('lex-runtime')

	query = event['q']
	
	if query == "voiceSearch":
		transcribe = boto3.client('transcribe')
		job_name = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime()).replace(":", "-").replace(" ", "")
		job_uri = "https://s3.amazonaws.com/cc3-voices-a/test.mp3"
		transcribe.start_transcription_job(
		    TranscriptionJobName=job_name,
		    Media={'MediaFileUri': job_uri},
		    MediaFormat='mp3',
		    LanguageCode='en-US'
		)
		while True:
		    status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
		    if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
		        break
		    print("Not ready yet...")
		    time.sleep(5)
		print("Transcript URL: ", status)
		transcriptURL = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
		trans_text = requests.get(transcriptURL).json()
		
		print("Transcripts: ", trans_text)
		print(trans_text["results"]['transcripts'][0]['transcript'])
		
		s3client = boto3.client('s3')
		response = s3client.delete_object(
		    Bucket='cc3-voices-a',
		    Key='test.mp3'
		)
		query = trans_text["results"]['transcripts'][0]['transcript']
		s3client.put_object(Body=query, Bucket='cc3-voices-a', Key='test.txt')
		return {
			'statusCode': 200,
			'headers': {
				"Access-Control-Allow-Origin": "*"
			},
			'body': "transcribe done"
		}
	
	if query == "voiceResult":
		s3client = boto3.client('s3')
		data = s3client.get_object(Bucket='cc3-voices-a', Key='test.txt')
		query = data.get('Body').read().decode('utf-8')
		print("Voice query: ", query)
		s3client.delete_object(
			Bucket='cc3-voices-a',
			Key='test.txt'
		)
		
	print('lex' + " " + query)
	lex_response = lex.post_text(
		botName='QuerySearch',
		botAlias='querySearch',
		userId= 'xyq',
		inputText=query
	)
	
	print("LEX RESPONSE --- {}".format(json.dumps(lex_response)))

	slots = lex_response['slots']

	img_list = []
	for i, tag in slots.items():
		if tag:
			print(tag)
			url = get_url('photos', 'Photo', tag)
			print("ES URL --- {}".format(url))

			es_response = requests.get(url, headers=headers).json()
			print("ES RESPONSE --- {}".format(json.dumps(es_response)))

			es_src = es_response['hits']['hits']
			print("ES HITS --- {}".format(json.dumps(es_src)))

			for photo in es_src:
				labels = [word.lower() for word in photo['_source']['labels']]
				if tag.lower() in labels:
					objectKey = photo['_source']['objectKey']
					img_url = 'https://assignment3b2.s3.amazonaws.com/' + objectKey
					img_list.append(img_url)
	
	img_list = set(img_list)
	ans = []
	for item in img_list:
		ans.append(item)
	if img_list:
		return {
			'statusCode': 200,
			'headers': {
				"Access-Control-Allow-Origin": "*",
				'Content-Type': 'application/json'
			},
			'body': ans
		}
	else:
		return {
			'statusCode': 200,
			'headers': {
				"Access-Control-Allow-Origin": "*",
				'Content-Type': 'application/json'
			},
			'body': json.dumps("No such photos.")
		}
