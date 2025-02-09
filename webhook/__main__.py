from constants import CHATBOT_URL, CHATBOT_PORT, WEBHOOK_ROUTE, PORT

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import requests
import warnings
warnings.filterwarnings("ignore")

app = FastAPI()

class GitHubWebhookData(BaseModel):
    ref: str | None = None

@app.post("/github-webhook")
async def github_webhook(data: GitHubWebhookData):
    print(data)
    response = await requests.post(CHATBOT_URL+":"+str(CHATBOT_PORT)+WEBHOOK_ROUTE, data)
    msg = ""
    if response.status_code == 200:
        msg = "Solicitud exitosa:"
        print(msg, response.json())
    else:
        msg = response.text
        print(f"Error {response.status_code}: {response.text}")
    return msg, response.status_code

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)