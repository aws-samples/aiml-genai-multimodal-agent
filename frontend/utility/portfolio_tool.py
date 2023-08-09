import pandas as pd
import datetime
import pandas as pd
from functools import reduce
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from langchain.tools import tool
from langchain.tools.base import StructuredTool
from typing import Optional
from langchain.tools import BaseTool
from typing import List, Optional
import json

with open ('param.json','r') as f:
    params=json.load(f)

class OptimizePortfolio(BaseTool):
    
    import pandas as pd
    
    name = "Portfolio Optimization Tool"
    description = """
        use this tool when you need to build optimal portfolio. 
        The output results tell you if you have $10,000, how many stocks of each one in the list you should buy.
        The stock_ls should be a list of stock symbols, such as ['WWW', 'DDD', 'AAAA'].
        """

    
    def _run(self, stock_ls: List):
        
        import boto3
        import pandas as pd
        from pyathena import connect
        
        # Establish connection to Athena
        session = boto3.Session(region_name=params['region'])
        athena_client = session.client('athena')

        # Execute query
        table='stock_prices'
        stock_seq = ', '.join(stock_ls)
        query = f'SELECT date, {stock_seq} from "{params["db"]}"."{table}"'
        print (f'query:{query}')
        cursor = connect(s3_staging_dir=f's3://{params["query_bucket"]}/athenaresults/', region_name=params["region"]).cursor()
        cursor.execute(query)

        # Fetch results
        rows = cursor.fetchall()

        # Convert to Pandas DataFrame
        df = pd.DataFrame(rows, columns=[column[0] for column in cursor.description])

        # Set "Date" as the index and parse it as a datetime object
        df.set_index("date", inplace=True)
        df.index = pd.to_datetime(df.index, format = '%Y-%m-%d')
        
        mu = expected_returns.mean_historical_return(df)
        S = risk_models.sample_cov(df)

        # Optimize for maximal Sharpe ratio
        ef = EfficientFrontier(mu, S)
        weights = ef.max_sharpe()
        ef.portfolio_performance(verbose=True)

        cleaned_weights = ef.clean_weights()
        print (f'cleaned_weights are {dict(cleaned_weights)}')

        ef.portfolio_performance(verbose=True)

        #Finally, let’s convert the weights into actual allocations values (i.e., how many of each stock to buy). For our allocation, let’s consider an investment amount of $100,000:

        from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices


        latest_prices = get_latest_prices(df)

        da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=10000)
        allocation, leftover = da.greedy_portfolio()
        print("Discrete allocation:", allocation)
        print("Funds remaining: ${:.2f}".format(leftover))
        print (allocation)
        return cleaned_weights

    def _arun(self, stock_ls: int):
        raise NotImplementedError("This tool does not support async")