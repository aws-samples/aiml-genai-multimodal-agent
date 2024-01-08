from langchain.retrievers import AmazonKendraRetriever
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import os
from langchain.chat_models import ChatAnthropic
import boto3
from botocore.exceptions import ClientError
import json
from langchain.llms.bedrock import Bedrock

with open ('param.json','r') as f:
    params=json.load(f)
    


kendra_index_id=params['kendra_id']
region=params['region']
def build_chain():

    inference_modifier = {'max_tokens_to_sample':512, 
                      "temperature":0.1,                     
                     }

    llm = llm = Bedrock(model_id='anthropic.claude-v2', model_kwargs = inference_modifier )
       
    retriever = AmazonKendraRetriever(index_id=params['kendra_id'], region_name=region, top_k=1)

    prompt_template = """ Context: {context}

    ONLY provide answers according to the context provided above! PAY great attention to useful information and provide a succint answer.
    If the answer is not in the context, response with "The answer is not found in the context provided". DONT make up answers!
    
    According to the context provided, {question}

    """      
    
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
