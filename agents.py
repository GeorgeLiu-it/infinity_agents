import os
import getpass
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import tool
import asyncio
import psycopg2

# MCP SDK
# from mcp.client import ClientSession
# from mcp.client.websocket import websocket_client

# Load environment variables
load_dotenv()

if not os.environ.get("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter API key for DeepSeek: ")

# Tavily Search
search = TavilySearch(max_results=2)

@tool("web_search", return_direct=False)
def search_tool(query: str) -> str:
    """Use this tool when you need to search the web for up-to-date or general information."""
    return search.invoke(query)

# Example MCP time tool (simulate remote MCP server)
@tool("time_tool", return_direct=False)
def time_tool(_: str = "") -> str:
    """Use this tool ONLY when the user asks for the current date or time."""
    # Example output as if it came from MCP server
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"The current server time is {now}"

# Get data from PostgreSQL
@tool("query_postgres_tool", return_direct=False)
def query_postgres(query: str) -> str:
    """
    Executes a SQL query on the 'personal_info' table in the MCP PostgreSQL database.
    Example input: "SELECT * FROM personal_info LIMIT 5;"
    """
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT", 5432)
        )
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return str(rows)
    except Exception as e:
        return f"Error querying database: {str(e)}"

# Regist tools
tools = [search_tool, time_tool, query_postgres]

# Initialize model
model = init_chat_model("deepseek-chat", model_provider="deepseek")
model_with_tools = model.bind_tools(tools)
from langchain.tools import tool

# Initialize agent + memory
memory = MemorySaver()
agent_executor = create_react_agent(model, tools, checkpointer=memory)


def run_agent(user_message: str, thread_id: str = "default-thread"):
    """
    Receives user input, calls DeepSeek + Tavily Agent, and returns the result.
    """
    print("start")
    config = {"configurable": {"thread_id": thread_id}}
    input_message = {"role": "user", "content": user_message}

    response = agent_executor.invoke({"messages": [input_message]}, config)
    print("agent execution end")
    
    return response

if __name__ == "__main__":
    user_query = "Please query today's weather information"
    result = run_agent(user_query)
    print("Agent returned result:", result)
