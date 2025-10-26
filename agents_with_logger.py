import os
import getpass
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import tool
import psycopg2, requests
import logging
from datetime import datetime
import json
from agent_config import (
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_THREAD_ID
)

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient, load_mcp_tools

@asynccontextmanager
async def lifespan(app: FastAPI):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "server/math.py")

    client = MultiServerMCPClient({
        "remote_mcp": {"url": "http://106.13.91.222:8000/sse", "transport": "sse"},
        "weather": {"url": "http://localhost:8000/sse", "transport": "sse"},
        "notion": {"url": "https://mcp.notion.com/sse", "transport": "sse"},
        "math": {"command": "/home/george/mcp_langchain/.venv/bin/python", "args": [server_path], "transport": "stdio"},
    })

    # Open both sessions and keep them alive
    async with client.session("math") as math_sess, client.session("weather") as weather_sess, client.session("remote_mcp") as remote_mcp_sess, client.session("notion") as notion_sess:
        m_tools = await load_mcp_tools(math_sess)
        w_tools = await load_mcp_tools(weather_sess)
        r_tools = await load_mcp_tools(remote_mcp_sess)
        n_tools = await load_mcp_tools(notion_sess)
        all_tools = m_tools + w_tools + r_tools + n_tools + tools

        app.state.agent_executor = create_react_agent(model, all_tools, checkpointer=memory)

        # ✅ Yield control back to FastAPI; sessions stay open
        yield

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

logger.info("🔧 Initializing AI Agents Environment...")

if not os.environ.get("DEEPSEEK_API_KEY"):
    logger.info("🔑 Prompting for DeepSeek API key...")
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter API key for DeepSeek: ")
    logger.info("✅ DeepSeek API key configured")

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8080")
logger.info(f"🌐 MCP Server URL: {MCP_SERVER_URL}")

# MCP Personal Info Checker Tool
@tool("mcp_query_personal_info", return_direct=False)
def mcp_query_personal_info(email: str) -> str:
    """
    Queries the MCP server for personal info by email address.
    Example input: "ethan.williams245@example.com"
    """
    logger.info(f"📧 MCP Tool: Querying personal info for email: {email}")
    try:
        endpoint = f"{MCP_SERVER_URL}/personal_info"
        logger.info(f"🌐 Making HTTP GET request to: {endpoint}")
        
        response = requests.get(endpoint, params={"email": email})
        logger.info(f"📡 HTTP Response Status: {response.status_code}")
        
        response.raise_for_status()
        data = response.json()
        logger.info(f"✅ MCP Query Successful - User found: {data.get('first_name')} {data.get('last_name')}")

        # Pretty formatting for LLM readability
        formatted = (
            f"✅ Personal Information Found:\n"
            f"- Name: {data.get('first_name')} {data.get('last_name')}\n"
            f"- Email: {data.get('email')}\n"
            f"- Phone: {data.get('phone')}\n"
            f"- DOB: {data.get('dob')}\n"
            f"- Address: {data.get('street_address')}, {data.get('city')}, "
            f"{data.get('state')} {data.get('postal_code')}, {data.get('country')}"
        )
        return formatted

    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            logger.warning(f"❌ MCP Query: No user found with email: {email}")
            return f"❌ No user found with email: {email}"
        logger.error(f"⚠️ MCP Query HTTP error: {str(e)}")
        return f"⚠️ HTTP error: {str(e)}"

    except Exception as e:
        logger.error(f"💥 MCP Query Error: {str(e)}", exc_info=True)
        return f"⚠️ Error querying MCP server: {e}"

# Tavily Search
logger.info("🔍 Initializing Tavily Search...")
search = TavilySearch(max_results=2)

@tool("web_search", return_direct=False)
def search_tool(query: str) -> str:
    """Use this tool when you need to search the web for up-to-date or general information."""
    logger.info(f"🌐 Web Search Tool: Executing query - '{query}'")
    try:
        result = search.invoke(query)
        logger.info(f"✅ Web Search Completed - Result length: {len(result)} characters")
        logger.debug(f"📄 Web Search Result Preview: {result[:200]}...")
        return result
    except Exception as e:
        logger.error(f"💥 Web Search Error: {str(e)}", exc_info=True)
        return f"Error performing web search: {str(e)}"

# Example MCP time tool (simulate remote MCP server)
@tool("time_tool", return_direct=False)
def time_tool(_: str = "") -> str:
    """Use this tool ONLY when the user asks for the current date or time."""
    logger.info("⏰ Time Tool: Getting current time")
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"✅ Time Tool Result: {now}")
    return f"The current server time is {now}"

# Get data from PostgreSQL
@tool("query_postgres_tool", return_direct=False)
def query_postgres(query: str) -> str:
    """
    Executes a SQL query on the 'personal_info' table in the MCP PostgreSQL database.
    Example input: "SELECT * FROM personal_info LIMIT 5;"
    """
    logger.info(f"🗄️ PostgreSQL Tool: Executing query - '{query}'")
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT", 5432)
        )
        logger.info("✅ Database connection established")
        
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ PostgreSQL Query Successful - Rows returned: {len(rows)}")
        logger.debug(f"📊 Query Result: {rows}")
        return str(rows)
        
    except Exception as e:
        logger.error(f"💥 PostgreSQL Query Error: {str(e)}", exc_info=True)
        return f"Error querying database: {str(e)}"

# Register tools
tools = [search, time_tool, query_postgres, mcp_query_personal_info]
logger.info(f"🛠️ Registered {len(tools)} tools: {[tool.name for tool in tools]}")

# Initialize model
logger.info("🤖 Initializing DeepSeek Chat Model...")
logger.info(f"🤖 Using system prompt from agent_config.py")
model = init_chat_model("deepseek-chat", model_provider="deepseek")
logger.info("✅ DeepSeek model initialized")

model_with_tools = model.bind_tools(tools)
logger.info("🔗 Tools bound to model")

# Initialize agent + memory
logger.info("🧠 Initializing Agent Memory...")
memory = MemorySaver()
logger.info("✅ Memory system initialized")

logger.info("⚙️ Creating ReAct Agent...")
agent_executor = create_react_agent(model, tools, checkpointer=memory)
logger.info("✅ ReAct Agent created successfully")


async def run_agent(request: Request, user_message: str, thread_id: str = DEFAULT_THREAD_ID):
    """
    Receives user input, calls DeepSeek + Tavily Agent, and returns the result.
    """
    logger.info("=" * 80)
    logger.info("🚀 STARTING AGENT EXECUTION")
    logger.info(f"💬 User Input: '{user_message}'")
    logger.info(f"🧵 Thread ID: {thread_id}")
    
    config = {"configurable": {"thread_id": thread_id}}
    input_message = [
        {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    logger.info("🔄 Invoking agent executor...")
    start_time = datetime.now()
    
    try:
        # response = agent_executor.invoke({"messages": input_message}, config)
        executor = request.app.state.agent_executor
        response = await executor.ainvoke({"messages": input_message}, config)
        process_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ AGENT EXECUTION COMPLETED")
        logger.info(f"⏱️  Execution Time: {process_time:.2f} seconds")
        
        # Log the agent's response structure
        if "messages" in response:
            last_message = response["messages"][-1] if response["messages"] else {}
            logger.info(f"📤 Agent Response Type: {type(last_message)}")
            if hasattr(last_message, 'content'):
                logger.info(f"💭 Agent Response Preview: {last_message.content[:200]}...")
        
        logger.info("=" * 80)
        return response
        
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"💥 AGENT EXECUTION FAILED")
        logger.error(f"⏱️  Failed after: {process_time:.2f} seconds")
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        logger.info("=" * 80)
        raise


if __name__ == "__main__":
    logger.info("🎯 STARTING MAIN EXECUTION")
    
    # Test different types of queries
    test_queries = [
        "Please query today's weather information",
        "What time is it now?",
        "Show me all users in the database",
        "Find personal info for oliver.smith123@example.com"
    ]
    
    for i, user_query in enumerate(test_queries, 1):
        logger.info(f"🧪 TEST {i}/4: '{user_query}'")
        try:
            result = run_agent(user_query, f"test-thread-{i}")
            logger.info(f"✅ Test {i} completed successfully")
        except Exception as e:
            logger.error(f"❌ Test {i} failed: {str(e)}")
    
    logger.info("🏁 ALL TESTS COMPLETED")