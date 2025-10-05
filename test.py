from dotenv import load_dotenv

# Load .env file
load_dotenv()


import os
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

print("API Key:", DEEPSEEK_API_KEY[:5] + "*****", tavily_key)

from langchain_tavily import TavilySearch

search = TavilySearch(max_results=2)
search_results = search.invoke("What is the weather in SF")
print(search_results)
# If we want, we can create other tools.
# Once we have all the tools we want, we can put them in a list that we will reference later.
tools = [search]

from langchain.chat_models import init_chat_model

model = init_chat_model("deepseek-chat", model_provider="deepseek")

query = "Hi!"
response = model.invoke([{"role": "user", "content": query}])
response.text()

model_with_tools = model.bind_tools(tools)

query = "Hi!"
response = model_with_tools.invoke([{"role": "user", "content": query}])

print(f"Message content: {response.text()}\n")
print(f"Tool calls: {response.tool_calls}")


query = "Search for the weather in SF"
response = model_with_tools.invoke([{"role": "user", "content": query}])

print(f"Message content: {response.text()}\n")
print(f"Tool calls: {response.tool_calls}")

from langgraph.prebuilt import create_react_agent

agent_executor = create_react_agent(model, tools)

input_message = {"role": "user", "content": "Search for the weather in SF"}
response = agent_executor.invoke({"messages": [input_message]})

for message in response["messages"]:
    message.pretty_print()

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

agent_executor = create_react_agent(model, tools, checkpointer=memory)

config = {"configurable": {"thread_id": "abc123"}}

for step in agent_executor.stream(
    {"messages": [("user", "What is my name?Besides of that, please tell me the SF weather like today?")]}, config, stream_mode="values"
):
    step["messages"][-1].pretty_print()
