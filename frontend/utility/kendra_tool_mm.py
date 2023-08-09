from langchain.retrievers import AmazonKendraRetriever
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import os
from langchain.chat_models import ChatAnthropic
import boto3
from botocore.exceptions import ClientError
import json

with open ('param.json','r') as f:
    params=json.load(f)
    
def get_secret():

    secret_name = "anthropic_key"
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']

    return json.loads(secret)

ANTHROPIC_API_KEY = get_secret()['anthropic_key']
kendra_index_id=params['kendra_id']

def build_chain():

    llm = ChatAnthropic(temperature=0, anthropic_api_key=ANTHROPIC_API_KEY, max_tokens_to_sample = 512)
       
    retriever = AmazonKendraRetriever(index_id=kendra_index_id)

    prompt_template = """

      Human: This is a friendly conversation between a human and an AI. 
      The AI is talkative and provides specific details from its context but limits it to 240 tokens.
      If the AI does not know the answer to a question, it truthfully says it does not know.

      Net income can be net loss. If the value is in paranthesis, it means it is a loss and hence a negative value. For example, (1000) means -1000.
    
      
      Assistant: OK, got it, I'll be a talkative truthful AI assistant.

      Human: Here are a few documents: {context}
      Based on the above documents, provide a straightforward answer for {question}. 
      Answer "don't know" if not present in the document. 

      Assistant:"""
    
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    chain_type_kwargs = {"prompt": PROMPT}
 
    return RetrievalQA.from_chain_type(
        llm, 
        chain_type="stuff", 
        retriever=retriever, 
        chain_type_kwargs=chain_type_kwargs,
        return_source_documents=True
    )


def run_chain(prompt: str, history=[]):
    chain = build_chain()
    result = chain(prompt)
    return {
        "answer": result['result'],
        "source_documents": result['source_documents']
    }
