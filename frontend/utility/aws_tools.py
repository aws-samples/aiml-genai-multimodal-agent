import boto3
import json

def SentimentAnalysis(inputString, region_name='us-east-2'):
    print(inputString)
    lambda_client = boto3.client('lambda')
    lambda_payload = {"inputString:"+inputString}
    response=lambda_client.invoke(FunctionName='FSI-SentimentDetecttion',
                        InvocationType='RequestResponse',
                     Payload=json.dumps(inputString))
    print(response['Payload'].read())
    return response

def DetectKeyPhrases(inputString, region_name='us-east-2'):
    print(inputString)
    lambda_client = boto3.client('lambda')
    lambda_payload = {"inputString:"+inputString}
    response=lambda_client.invoke(FunctionName='FSI-KeyPhrasesDetection',
                        InvocationType='RequestResponse',
                     Payload=json.dumps(inputString))
    print(response['Payload'].read())
    return response

def IntiateTextExtractProcessing(inputString, region_name='us-east-2'):
    print(inputString)
    lambda_client = boto3.client('lambda')
    lambda_payload = {"inputString:"+inputString}
    response=lambda_client.invoke(FunctionName='FSI-TextractAsyncInvocationFunction',
                        InvocationType='RequestResponse',
                     Payload=json.dumps(inputString))
    #print(response['Payload'].read())
    return response

def TranscribeAudio(inputString, region_name='us-east-2'):
    print(inputString)
    lambda_client = boto3.client('lambda')
    lambda_payload = {"inputString:"+inputString}
    response=lambda_client.invoke(FunctionName='FSI-Transcribe',
                        InvocationType='RequestResponse',
                     Payload=json.dumps(inputString))
    print(response['Payload'].read())
    return response
