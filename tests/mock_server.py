import sys
import json

def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

while True:
    line = sys.stdin.readline()
    if not line:
        break
    msg = json.loads(line.strip())
    method = msg.get("method")
    req_id = msg.get("id")

    if method == "initialize":
        send({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "capabilities": {"tools": True},
                "serverInfo": {"name": "mock-server", "version": "1.0"},
            }
        })
    elif method == "tools/list":
        send({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {"name": "echo", "description": "Echo back a message"},
                    {"name": "sum", "description": "Add two numbers"},
                ]
            }
        })
    else:
        send({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method {method}"},
        })
