import os
import logging
import uvicorn
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()

FastAPIInstrumentor().instrument_app(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
def rootPage():
    logger.info("rootPage accessed")
    return "Hello World"

if __name__ == "__main__":
    """
    디버깅을 위해 역으로 파이썬 안에서 Uvicorn을 호출
    """
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=int(os.environ.get("UVICORN_PORT", 8111))
    )