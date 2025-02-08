import os
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def rootPage():
    return "Hello World"
