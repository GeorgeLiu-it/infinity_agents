from fastapi import FastAPI, Request
import uvicorn
import os
import getpass
import time
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

import psycopg2
from langchain.tools import tool

# 加载环境变量
load_dotenv()

if not os.environ.get("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter API key for DeepSeek: ")


@tool
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


# Tavily 搜索
search = TavilySearch(max_results=2)
tools = [search, query_postgres]

# 初始化模型
model = init_chat_model("deepseek-chat", model_provider="deepseek")
model_with_tools = model.bind_tools(tools)

# 初始化 agent + memory
memory = MemorySaver()
agent_executor = create_react_agent(model, tools, checkpointer=memory)

app = FastAPI()

@app.post("/webhook/message")
async def webhook_message(request: Request):
    body = await request.json()
    print(body)
    user_message = body.get("message", "")

    if not user_message:
        return {"error": "Missing 'message' in request body"}

    config = {"configurable": {"thread_id": "abc123"}}
    input_message = {"role": "user", "content": user_message}
    print("start")
    response = agent_executor.invoke({"messages": [input_message]}, config)
    time.sleep(1)
    print(response)
    return {"response": response["messages"][-1].content,
            "tools": None
            }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=443,
        ssl_certfile="certs/certificate.crt",   # 证书路径
        ssl_keyfile="certs/private.key"      # 私钥路径
    )
