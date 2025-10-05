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

# 加载环境变量
load_dotenv()

if not os.environ.get("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter API key for DeepSeek: ")

# Tavily 搜索
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

# --- Add MCP client tool ---
class MCPTool:
    def __init__(self, url: str):
        self.url = url
        self.session: ClientSession | None = None

    async def connect(self):
        """连接 MCP WebSocket"""
        async with websocket_client(self.url) as (read, write):
            self.session = ClientSession(read, write)
            await self.session.initialize()

    async def query(self, query: str) -> str:
        if not self.session:
            raise RuntimeError("MCP session not connected. Call connect() first.")
        # 假设 MCP 服务器上有一个工具名为 "query"
        result = await self.session.call_tool("query", {"input": query})
        return str(result)

# Example remote public MCP server
mcp_tool = MCPTool("wss://mcp.openai.com/weather")
# 在程序启动时连接 MCP
# asyncio.run(mcp_tool.connect())

# Example remote MCP tool (placeholder)
@tool("mcp_tool", return_direct=False)
def mcp_tool_run(query: str) -> str:
    """通过 MCP 查询远程数据"""
    try:
        return asyncio.run(mcp_tool.query(query))
    except Exception as e:
        return f"MCP error: {str(e)}"


# Regist tools
tools = [search_tool, time_tool, mcp_tool_run]

# 初始化模型
model = init_chat_model("deepseek-chat", model_provider="deepseek")
model_with_tools = model.bind_tools(tools)
from langchain.tools import tool

# 初始化 agent + memory
memory = MemorySaver()
agent_executor = create_react_agent(model, tools, checkpointer=memory)


def run_agent(user_message: str, thread_id: str = "default-thread"):
    """
    接收用户输入，调用 DeepSeek + Tavily Agent，并返回结果
    """
    print("start")
    config = {"configurable": {"thread_id": thread_id}}
    input_message = {"role": "user", "content": user_message}

    response = agent_executor.invoke({"messages": [input_message]}, config)
    print("agent execution end")
    
    return response

if __name__ == "__main__":
    user_query = "请查询今天的天气信息"
    result = run_agent(user_query)
    print("Agent 返回结果：", result)
