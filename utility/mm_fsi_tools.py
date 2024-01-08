from langchain.agents.tools import Tool
from langchain_experimental.plan_and_execute import PlanAndExecute, load_agent_executor, load_chat_planner
from langchain.tools.python.tool import PythonREPLTool
import aws_tools, kendra_tool_mm, portfolio_tool, stock_query_mm
from stock_query_mm import 

tools = [
    Tool(
        name="Stock Querying Tool",
        func=run_query,
        description="""
        Useful for when you need to answer questions about stocks. It only has information about stocks.
        """
    ),
    OptimizePortfolio(),
    Tool(
        name="Financial Information Lookup Tool",
        func=run_chain,
        description="""
        Useful for when you need to look up financial information using kendra. 
        """
    ),
    PythonREPLTool(),
    Tool(
        name="Sentiment Analysis Tool",
        func=SentimentAnalysis,
        description="""
        Useful for when you need to analyze the sentiment of a topic, such as "Return to Office".
        """
    ),
     Tool(
        name="Detect Phrases Tool",
        func=DetectKeyPhrases,
        description="""
        Useful for when you need to detect key phrases in recent quaterly reports.
        """
    ),
     Tool(
        name="Text Extraction Tool",
        func=IntiateTextExtractProcessing,
        description="""
        Useful for when you need to trigger conversion of  pdf version of quaterly reports to text files using amazon textextract
        """
    ),
     Tool(
        name="Transcribe Audio Tool",
        func=TranscribeAudio,
        description="""
        Useful for when you need to convert audio recordings of earnings calls from audio to text format using Amazon Transcribe
        """
    )
]