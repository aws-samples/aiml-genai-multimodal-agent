import boto3
import json

with open ('param.json','r') as f:
    params=json.load(f)
    

REGION=params['region']
def SentimentAnalysis(inputString):
    print(inputString)
    lambda_client = boto3.client('lambda', region_name=REGION)
    lambda_payload = {"inputString:"+inputString}
    response=lambda_client.invoke(FunctionName='FSI-SentimentDetecttion',
                        InvocationType='RequestResponse',
                     Payload=json.dumps(inputString))
    #print(response['Payload'].read())
    output=json.loads(response['Payload'].read().decode())
    return output['body']

def DetectKeyPhrases(inputString):
    #print(inputString)
    lambda_client = boto3.client('lambda', region_name=REGION)
    lambda_payload = {"inputString:"+inputString}
    response=lambda_client.invoke(FunctionName='FSI-KeyPhrasesDetection',
                        InvocationType='RequestResponse',
                     Payload=json.dumps(inputString))
    #print(response['Payload'].read())
    output=json.loads(response['Payload'].read().decode())
    return output['body']

def IntiateTextExtractProcessing(inputString):
    print(inputString)
    lambda_client = boto3.client('lambda', region_name=REGION)
    lambda_payload = {"inputString:"+inputString}
    response=lambda_client.invoke(FunctionName='FSI-TextractAsyncInvocationFunction',
                        InvocationType='RequestResponse',
                     Payload=json.dumps(inputString))
    #print(response['Payload'].read())
    return response

def TranscribeAudio(inputString):
    print(inputString)
    lambda_client = boto3.client('lambda', region_name=REGION)
    lambda_payload = {"inputString:"+inputString}
    response=lambda_client.invoke(FunctionName='FSI-Transcribe',
                        InvocationType='RequestResponse',
                     Payload=json.dumps(inputString))
    print(response['Payload'].read())
    return response
