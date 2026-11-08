import pytest
from fastapi.testclient import TestClient
from app.main import app

HEADERS = {"Accept":"application/json, text/event-stream"}


def test_http_lifecycle_and_origins():
    with TestClient(app) as client:
        response = client.post("/mcp", headers=HEADERS, json={"jsonrpc":"2.0","id":1,"method":"initialize"})
        assert response.status_code == 200
        assert response.json()["result"]["protocolVersion"] == "2025-03-26"
        assert client.post("/mcp",headers={**HEADERS,"Origin":"https://attacker.example"},json={"jsonrpc":"2.0","id":2,"method":"ping"}).status_code==403
        assert client.post("/mcp",headers={**HEADERS,"Host":"attacker.example"},json={"jsonrpc":"2.0","id":2,"method":"ping"}).status_code==400
        assert client.post("/mcp",headers=HEADERS,json={"jsonrpc":"2.0","method":"notifications/initialized"}).status_code==202
        assert client.get("/mcp").status_code==405
        tools=client.post("/mcp",headers=HEADERS,json={"jsonrpc":"2.0","id":3,"method":"tools/list"}).json()
        assert len(tools["result"]["tools"])==2
        deny=client.post("/mcp",headers=HEADERS,json={"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"get_system_incident_history","arguments":{"system_id":"SYS-HR-001"}}}).json()
        assert deny["error"]["code"] == -32001


def test_malformed_http_messages():
    with TestClient(app) as client:
        assert client.post("/mcp",json={}).status_code==406
        assert client.post("/mcp",headers={**HEADERS,"Content-Type":"application/json"},content="{").status_code==400
        assert client.post("/mcp",headers=HEADERS,json=[]).status_code==400
        assert client.post("/mcp",headers=HEADERS,json="x"*1048576).status_code==413
