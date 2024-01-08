import boto3
from typing import List



def get_cfn_outputs(stackname: str, region) -> List:
    cfn = boto3.client('cloudformation', region_name=region)
    outputs = {}
    for output in cfn.describe_stacks(StackName=stackname)['Stacks'][0]['Outputs']:
        outputs[output['OutputKey']] = output['OutputValue']
    return outputs

# this function extracts the bucket name from S3 uri.
# For example, the bucket name is 'my_bucket' based on the URI "s3://my_bucket/"
def get_bucket_name(s3_uri):
    bucket_name = s3_uri.split("/")[2]
    return bucket_name

def stack_info(cfn_stack_name, region):
    stacks = boto3.client('cloudformation', region_name=region).list_stacks()
    stack_found = cfn_stack_name in [stack['StackName'] for stack in stacks['StackSummaries']]

    if stack_found is True:
        outputs = get_cfn_outputs(cfn_stack_name, region)
        glue_db_name = outputs['stockpricesdb']
        kendra_index_id = outputs['KendraIndexId']
        audio_transcripts_source_bucket = get_bucket_name(outputs['AudioSourceBucket'])
        textract_source_bucket = get_bucket_name(outputs['PDFSourceBucket'])
        query_staging_bucket = get_bucket_name(outputs['QueryStagingBucket'])    
        multimodal_output_bucket = get_bucket_name(outputs['MultimodalOutputBucket'])  
        return glue_db_name,kendra_index_id,audio_transcripts_source_bucket,textract_source_bucket,query_staging_bucket,multimodal_output_bucket
        
    else:
        return print("Recheck your cloudformation stack name")