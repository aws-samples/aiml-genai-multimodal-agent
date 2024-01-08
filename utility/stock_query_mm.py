from langchain import PromptTemplate,SQLDatabase, LLMChain
from langchain_experimental.sql.base import SQLDatabaseChain
from langchain.prompts.prompt import PromptTemplate
import boto3
from botocore.exceptions import ClientError
import json
from sqlalchemy import create_engine
from langchain.llms.bedrock import Bedrock

with open ('param.json','r') as f:
    params=json.load(f)
    

inference_modifier = {'max_tokens_to_sample':512, 
                      "temperature":0,
                        # "stop_sequences":["\n\nQuestion:","\n\nHuman:"] 
                     }

llm = Bedrock(model_id='anthropic.claude-v2', model_kwargs = inference_modifier )

# Modify the following parameters as needed
table = 'stock_prices'

connathena=f"athena.{params['region']}.amazonaws.com" 
portathena='443' #Update, if port is different
schemaathena=params["db"] #from user defined params
s3stagingathena=f's3://{params["query_bucket"]}/athenaresults/'#from cfn params
wkgrpathena='primary'#Update, if workgroup is different

##  Create the athena connection string
connection_string = f"awsathena+rest://@{connathena}:{portathena}/{schemaathena}?s3_staging_dir={s3stagingathena}&work_group={wkgrpathena}"

##  Create the athena  SQLAlchemy engine
engine_athena = create_engine(connection_string, echo=False)
dbathena = SQLDatabase(engine_athena)


_DEFAULT_TEMPLATE ="""
First, you understand the question being asked of you, then you perform one of two task depending on the information provided to you:
1. Assuming a role of a SQL developer, generate SQL statements. Only provide the sql statements alone and no additional text.
2. Assuming the role of an assistant, provide a clear and direct answer to the question.

Assistant: 
I understand my role and task. I would understand the question and either provide a sql statement or a natural language answer depending on the information I am provided.

Human:    
Here are certain nuances to questions that you should pay attention to:
1. If a question ask for "closing prices", it should be the last price at which a stock trades for the given time period. For example if the time period in the question is 2020, then the closing price is the price for the last available date in 2020.

Assistant: 
Thank you for the clarification. I would treat any questions with "closing prices" as the last price for the given date period.

Human:    
Here is a schema of a table:
<schema>
{table_info}
</schema>       

When providing your response:   
1. If "SQLResult" is not provided, your response should only contain the SQL statement as additional non-sql text would cause Athena to throw an error.
2. If "SQLResult" is provided, your response should be based off the context in "SQLResult" as a financial expert.

Assistant:   
Yes, if there is not a SQLResult information provided that tells me that I would be only providing SQL statements alone as additional text would cause Amazon Athena to throw an error.
However, if SQLResult is provided to me, I would only provide answers to the question based off the SQLResult context after understanding the question from a financial experts view.

Human:
Question: {input}
SQLQuery:"""

def run_query(query):

    PROMPT_sql = PromptTemplate(
        input_variables=["input", "table_info"], template=_DEFAULT_TEMPLATE
    )
    
    db_chain = SQLDatabaseChain.from_llm(llm, dbathena, prompt=PROMPT_sql, verbose=True, return_intermediate_steps=False)
    response=db_chain.run(query)
    
    return response