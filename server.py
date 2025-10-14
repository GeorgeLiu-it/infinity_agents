from fastapi import FastAPI, Request
import uvicorn
from agents_with_logger import run_agent

app = FastAPI()

@app.post("/webhook/message")
async def webhook_message(request: Request):
    body = await request.json()
    user_message = body.get("message", "hello")
    prompt_id = body.get("prompt_id", "")

    response = run_agent(user_message, thread_id=prompt_id)
    
    print(response)

    return {"response": response["messages"][-1].content,
            "tools": response["messages"][-2].name
            }


@app.post("/webhook/test")
async def interaction(request: Request):
    """
    New API endpoint:
    Receives JSON with message, uuid, prompt_id
    Calls run_agent() and returns standard response format
    """
    body = await request.json()

    user_message = body.get("message")

    if not user_message:
        return {"error": "Missing required field: message"}

    # Call the agent
    # agent_response = run_agent(user_message, thread_id=body.get("uuid", "default-thread"))

    # Standardized response format
    return {
        "response": "Glad to help you here! \n Your message is: " + user_message,
        "tools": None
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=443,
        ssl_certfile="certs/certificate.crt",   # Certificate Path
        ssl_keyfile="certs/private.key"      # Private Key Path
    )
