from langchain import PromptTemplate,SQLDatabase, SQLDatabaseChain, LLMChain
from langchain.prompts.prompt import PromptTemplate
import boto3
from botocore.exceptions import ClientError
import json
from langchain.chat_models import ChatAnthropic
from sqlalchemy import create_engine

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
llm = ChatAnthropic(temperature=0, anthropic_api_key=ANTHROPIC_API_KEY, max_tokens_to_sample = 512)

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


_DEFAULT_TEMPLATE = """
    Given an input question, first create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
    
    Do not append 'Query:' to SQLQuery.
    
    For example, if I want to get stock price information for aaaa, gg and ddd, the query should be :
    
    SELECT date, aaaa, gg, ddd FROM "blog-stock-prices-db"."stock_prices" order by date asc
    
    Display SQLResult after the query is run in plain english that users can understand. 
    

    Provide answer in simple english statement.
 
    Only use the following tables:

    {table_info}
    If someone asks about closing price of a stock, it should be the last price at which a stock trades during a regular trading session.
    
    Question: {input}
    
    Provide answer to the input question based on the query results.  
    """

def run_query(query):

    PROMPT_sql = PromptTemplate(
        input_variables=["input", "table_info", "dialect"], template=_DEFAULT_TEMPLATE
    )
    
    db_chain = SQLDatabaseChain.from_llm(llm, dbathena, prompt=PROMPT_sql, verbose=True, return_intermediate_steps=False)
    response=db_chain.run(query)
    
    return response