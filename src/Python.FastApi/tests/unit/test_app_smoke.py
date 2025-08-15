""" 
Basic smoke tests for the FastAPI application. 
Contract: - GET / should return 200 and a JSON string body. 
Edge cases covered: - Endpoint availability. 
""" 
import sys
from pathlib import Path
# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient 
# Import the FastAPI app instance 
from app import app 

client = TestClient(app) 
def test_root_returns_ok_and_expected_body() -> None: 
	resp = client.get("/") 
	assert resp.status_code == 200 
	# FastAPI will JSON-serialize a top-level str return value 
	assert resp.json() == "Python.FastAPI Backend Server"