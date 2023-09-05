import boto3
from botocore.exceptions import ClientError
import json
import langchain
from importlib import reload
reload(langchain)
from langchain.agents.structured_chat import output_parser
reload(output_parser)
from typing import List
import logging
import os
import sqlalchemy
from sqlalchemy import create_engine
from langchain.docstore.document import Document
from langchain import PromptTemplate,SQLDatabase, LLMChain
from langchain_experimental.sql.base import SQLDatabaseChain
from langchain.prompts.prompt import PromptTemplate
import streamlit as st
from langchain.chat_models import ChatAnthropic
import pandas as pd
import datetime
from langchain.tools import tool
from typing import List, Optional

from langchain.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_experimental.plan_and_execute import PlanAndExecute, load_agent_executor, load_chat_planner
from langchain.agents.tools import Tool
import time
import uuid

from utility import stock_query_mm, kendra_tool_mm, aws_tools, portfolio_tool, custom_logga, upload_amz_file, get_cfn_details
from langchain.tools.python.tool import PythonREPLTool
from langchain.llms.bedrock import Bedrock
reload(aws_tools)
reload(portfolio_tool)
reload(kendra_tool_mm)
reload(upload_amz_file)
reload(custom_logga)
reload(stock_query_mm)
reload(get_cfn_details)

from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import DynamoDBChatMessageHistory
from streamlit.web.server.websocket_headers import _get_websocket_headers
import sys 

st.set_page_config(layout="wide")
# logger = logging.getLogger('sagemaker')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())

sys.stdout = custom_logga.Logger()


#Session states to hold sateful variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'ant_key' not in st.session_state:
    st.session_state['ant_key'] = ''
if 'chat_id' not in st.session_state:
    st.session_state['chat_id'] = 1
if 'client_id' not in st.session_state:
    st.session_state['client_id'] = ''
if 'prompt' not in st.session_state:
    st.session_state['prompt'] = ''
if 'memory' not in st.session_state:
    st.session_state['memory'] = ""
    
# Global Variables
STACK_NAME="mmfsigenai" #change to the name of the cloudformation stack
REGION='us-east-2' #change to the name of the region you are working in

from botocore.config import Config

config = Config(
    retries = dict(
        max_attempts = 10
    )
)

bedrock = boto3.client(service_name='bedrock',region_name='us-east-1',endpoint_url='https://bedrock.us-east-1.amazonaws.com', config=config)
    
if len(st.session_state['messages'])<1:  
    ## browser client info
    headers = _get_websocket_headers()
    st.session_state['client_id'] = str(headers.get("Sec-Websocket-Key"))
    #print(f"Client KEY {st.session_state['client_id']}")
    
    # Anthropic API key
    #st.session_state['ant_key']= get_secret()['anthropic_key']     
    st.session_state['chat_id']= st.session_state['chat_id']+1
    #print(f"Session Chat ID {st.session_state['chat_id']}")
    
    # get cfn parameters      
    glue_db_name,kendra_index_id,audio_transcripts_source_bucket,textract_source_bucket,query_staging_bucket,multimodal_output_bucket=get_cfn_details.stack_info(STACK_NAME)
    param={}
    param['db']=glue_db_name
    param['query_bucket']=query_staging_bucket
    param['region']=REGION
    param['kendra_id']=kendra_index_id
    
    #Store parameters in json file
    with open('param.json', 'w', encoding='utf-8') as f:
        json.dump(param, f, ensure_ascii=False, indent=4)

    # upload files to s3
    #from utility.upload_amz_file import upload_file_amz
    upload_amz_file.upload_file_amz('files/Amazon-10K-2022-EarningsReport.pdf', textract_source_bucket)
    upload_amz_file.upload_file_amz('files/Amazon-10Q-Q1-2023-QuaterlyEarningsReport.pdf', textract_source_bucket)
    upload_amz_file.upload_file_amz('files/Amazon-Quarterly-Earnings-Report-Q1-2023-Full-Call-v1.mp3', audio_transcripts_source_bucket)   

    
    #Athena connection config
    connathena=f"athena.{REGION}.amazonaws.com" 
    portathena='443' #Update, if port is different
    schemaathena=glue_db_name #from user defined params
    s3stagingathena=f's3://{query_staging_bucket}/athenaresults/'#from cfn params
    wkgrpathena='primary'#Update, if workgroup is different

    ##  Create the athena connection string
    connection_string = f"awsathena+rest://@{connathena}:{portathena}/{schemaathena}?s3_staging_dir={s3stagingathena}&work_group={wkgrpathena}"

    ##  Create the athena  SQLAlchemy engine
    engine_athena = create_engine(connection_string, echo=False)
    dbathena = SQLDatabase(engine_athena)
       



#ANTHROPIC_API_KEY=st.session_state['ant_key'] #persist api key 
inference_modifier = {'max_tokens_to_sample':512, 
                      "temperature":0,
                        "stop_sequences":["\n\nQuestion:"] 
                     }

llm = Bedrock(model_id='anthropic.claude-v2', model_kwargs = inference_modifier )
table = 'stock_prices'
chat_history_table = 'chat_history'
session_id=st.session_state['client_id']
chat_id= st.session_state['chat_id']

#persist dynamodb table id for chat history for each session and browser client
@st.cache_data
def db_table_id(session_id, chat_id):
    chat_sess_id=str(uuid.uuid4())
    return chat_sess_id

chat_session_id=db_table_id(session_id, chat_id)
#print(f"Chat SESSION ID {chat_session_id}")

def run_query(query):

    PROMPT_sql = PromptTemplate(
        input_variables=["input", "table_info", "dialect"], template=_DEFAULT_TEMPLATE
    )
    
    db_chain = SQLDatabaseChain.from_llm(llm, dbathena, prompt=PROMPT_sql, verbose=True, return_intermediate_steps=False)
    response=db_chain.run(query)
    
    return response

def SentimentAnalysis(inputString):
    print(inputString)
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    lambda_payload = {"inputString:"+inputString}
    response=lambda_client.invoke(FunctionName='FSI-SentimentDetecttion',
                        InvocationType='RequestResponse',
                     Payload=json.dumps(inputString))
    #print(response['Payload'].read())
    output=json.loads(response['Payload'].read().decode())
    return output['body']

def DetectKeyPhrases(inputString):
    #print(inputString)
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    lambda_payload = {"inputString:"+inputString}
    response=lambda_client.invoke(FunctionName='FSI-KeyPhrasesDetection',
                        InvocationType='RequestResponse',
                     Payload=json.dumps(inputString))
    #print(response['Payload'].read())
    output=json.loads(response['Payload'].read().decode())
    return output['body']


tools = [
    Tool(
        name="Stock Querying Tool",
        func=stock_query_mm.run_query,
        description="""
        Useful for when you need to answer questions about stocks. It only has information about stocks.
        """
    ),
    portfolio_tool.OptimizePortfolio(),
    Tool(
        name="Financial Information Lookup Tool",
        func=kendra_tool_mm.run_chain,
        description="""
        Useful for when you need to look up financial information like revenues, sales, loss, risks etc. 
        """
    ),
    PythonREPLTool(),
    Tool(
        name="Sentiment Analysis Tool",
        func=SentimentAnalysis,
        description="""
        Useful for when you need to analyze the sentiment of an excerpt from a financial report.
        """
    ),
     Tool(
        name="Detect Phrases Tool",
        func=DetectKeyPhrases,
        description="""
        Useful for when you need to detect key phrases in financial reports.
        """
    ),
     Tool(
        name="Text Extraction Tool",
        func=aws_tools.IntiateTextExtractProcessing,
        description="""
        Useful for when you need to trigger conversion of  pdf version of quaterly reports to text files using amazon textextract
        """
    ),
     Tool(
        name="Transcribe Audio Tool",
        func=aws_tools.TranscribeAudio,
        description="""
        Useful for when you need to convert audio recordings of earnings calls from audio to text format using Amazon Transcribe
        """
    )
]

combo_template = """
    Let's first understand the problem and devise a plan to solve the problem. 
    Please output the plan starting with the header 'Plan:' and then followed by a numbered list of steps. Do not use past conversation history when you are planning the steps.
    Please make the plan the minimum number of steps required to accurately complete the task.    
    
    These are guidance on when to use a tool to solve a task, follow them strictly:  
    
    - When you need to find stock information, use Stock Querying Tool , as it provides more accurate and relevant answers. Pay attention to the time period. DO NOT search for answers on the internet.
    
    - When you need to look up financial and business information (such as revenue, income, risk, highlights etc.) from a financial quartely/annual report, use the Financial Information Lookup Tool.
    
    - When you need to find the key phrases information, from information pertaining to the question retrieved from financial report using the Financial Information Lookup Tool,  then use Detect Phrases Tool to get the information about all key phrases and respond with key phrases relavent to the question.

    - When you need to provide an optimized stock portfolio based on stock names, use Portfolio Optimization Tool. The output is the percent of fund you should spend on each stock.
    
    - When you need to do maths calculations, use "PythonREPLTool()" which is based on the python programming language. Only provide the required numerical values to this tool and test, for e.g. "stock_prices": [25, 50, 75] only pass in [25, 50, 75] not the text "stock prices:"
    
    - When you need to analyze sentiment of a topic, from information pertaining to the question retrieved from financial report using the Financial Information Lookup Tool, use "Sentiment Analysis Tool" on the information from the "Financial Information Lookup Tool"
    
    
    "Closing price" means the most recent stock price of the time period.    
    
    Income can be a positive (profit) or negative value (loss). If the value is in parenthesis (), take it as negative value, which means it's a loss. E.g. for (1000), use -1000.
         
    When you have a question about calculating a ratio, figure out the formula for the calculation, and find the relevant financial information using the proper tool. Then use PythonREPLTool() tool for calculation.

    If you can't find the answer, say "I can't find the answer for this question."   
    
    
    Once you have answers for the question, stop and provide the final answers. The final answers should be a combination of the answers to all the questions, not just the last one.
    Do not include the tools used when providing your final answer. Provide a coherent final answer
    
    Please use these to construct an answer to the question , as though you were answering the question directly. Ensure that your answer is accurate and doesn’t contain any information not directly supported by the summary and quotes.
    If there are no data or information in this document that seem relevant to this question, please just say "I can’t find any relevant quotes".
    """

combo_template=combo_template if st.session_state['prompt']=="" else st.session_state['prompt']

model = llm

chat_history_memory = DynamoDBChatMessageHistory(table_name=chat_history_table, session_id=chat_session_id)
memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=chat_history_memory, return_messages=True)

planner = load_chat_planner(model)

system_message_prompt = SystemMessagePromptTemplate.from_template(combo_template)
human_message_prompt = planner.llm_chain.prompt.messages[1]
planner.llm_chain.prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

executor = load_agent_executor(model, tools, verbose=True)
if st.session_state['memory']:
    agent = PlanAndExecute(planner=planner, executor=executor, verbose=True, max_iterations=2, memory=memory)
else:
    agent = PlanAndExecute(planner=planner, executor=executor, verbose=True, max_iterations=2)#, memory=memory)


def query(request, agent, chat_history_memory):
    output=agent(request)
    chat_history_memory.add_ai_message(str(output))
    try:
        return output['output']
    except:
        return output



    
def action_doc(agent, chat_history_memory):
    st.title('Multi-Modal Agent to assist Financial Analyst')

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        if "role" in message.keys():
            with st.chat_message(message["role"]):            
                st.markdown(str(message["content"]).replace("$","USD ").replace("%", " percent"))
        else:
            with st.expander(label="**Intermediate Steps**"):
                st.write(message["steps"])
            
    if prompt := st.chat_input("Hello?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            output_answer=query(prompt, agent, chat_history_memory) 
            message_placeholder.markdown(str(output_answer).replace("$","USD ").replace("%", " percent"))
        st.session_state.messages.append({"role": "assistant", "content": output_answer})
        
        # Saving the intermediate steps in a logf file to be shown in the UI. This is a hack due to the inability to capture these steps with the agent planner and executor library being used
        with st.expander(label="**Intermediate Steps**"): 
            with open('logfile.txt','r')as f:
                steps=f.readlines()
                st.write(steps)
            os.remove('logfile.txt')
        st.session_state.messages.append({"steps": steps})
      
            
        
                    
            
def app_sidebar():
    with st.sidebar:
        st.write('## How to use:')
        description = """This app lets you query multi-modal documents and get relevant answers. 
                        Documents inculde DB Tables, audio files and pdf files.
                        Type your query in the chat box to get appropiate answers.
                        If you need to refresh session, click on the `Clear Session` button.
                        Happy QnA :)
                        """
        st.markdown(description)
        st.write('---')
        st.write('## Sample Questions')
        st.markdown("""
                    - What are the closing prices of stocks AAAA, WWW, DDD in year 2018? Can you build an optimized portfolio using these three stocks? Please provide answers to both questions.
                    - What is the net sales for Amazon in 2021 and 2022? What is the percent difference?
                    - What are the biggest risks facing Amazon Inc?                                  
                    """)
        st.markdown("""
                    **Datasets**
                    
                    - [Quterly Earnings recordings](https://github.com/revdotcom/speech-datasets)
                    - [Annual Reports (FinTabNet)](https://developer.ibm.com/exchanges/data/all/fintabnet/)
                    - [S&P 500 stock data](https://www.kaggle.com/camnugent/sandp500)
                    """)
        st.write('---')
        #st.write('Pass your custom prompt')
        user_input = st.text_area("Custom prompt goes here", "")
        if user_input:
            st.session_state['prompt']=user_input
        print(user_input)
        
        use_memory=''
        mem = st.checkbox('Conversation Memory')
        if mem:
            use_memory='yes' 
        st.session_state['memory']=use_memory
            
        if st.button('Clear Session'):
            '''
                The Clear context helps to refresh the UI and also create a new session for the chat. This creates a new Dynamo DB table to                   hold the chat history.
            ''' 
            # Delete all the items in Session state
            for key in st.session_state.keys():
                del st.session_state[key] 
            # create new session state items
            if 'generated' not in st.session_state:
                st.session_state['generated'] = []
            if 'past' not in st.session_state:
                st.session_state['past'] = []
            if 'messages' not in st.session_state:
                st.session_state['messages'] = []
            if 'ant_key' not in st.session_state:
                st.session_state['ant_key'] = ''
            if 'chat_id' not in st.session_state:
                st.session_state['chat_id'] = 1
            if 'client_id' not in st.session_state:
                st.session_state['client_id'] = ''
            if 'prompt' not in st.session_state:
                st.session_state['prompt'] = ""
            if 'memory' not in st.session_state:
                st.session_state['memory'] = ""

def main(agent,chat_history_memory):
    params=app_sidebar()
    action_doc(agent, chat_history_memory)


if __name__ == '__main__':
    main(agent, chat_history_memory)
