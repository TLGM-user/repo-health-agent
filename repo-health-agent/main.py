import os
from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.post("/webhook")
async def github_webhook(request: Request):
    event_type = request.headers.get("X-GitHub-Event")
    payload = await request.json()

    if event_type == "ping":
        return {"message": "Pong! Webhook active."}

    return {"status": "success"}
