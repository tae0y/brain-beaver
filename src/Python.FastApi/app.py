import os
import logging
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
#from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from extract.concepts.conceptshandler import router as concepts_router
from engage.networks.networkshandler import router as networks_router
from expand.references.referenceshandler import router as references_router


app = FastAPI(
    swagger_ui_parameters={
        "dom_id": "#swagger-ui"
    }
)

origins = [
    "http://127.0.0.1:8111"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(concepts_router)
app.include_router(networks_router)
app.include_router(references_router)

#FastAPIInstrumentor().instrument_app(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
def rootPage():
    logger.info("HOME PAGE ACCESS")
    return "Python.FastAPI Backend Server"

if __name__ == "__main__":
    """
    디버깅을 위해 역으로 파이썬 안에서 Uvicorn을 호출
    """
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=int(os.environ.get("UVICORN_PORT", 8111))
    )