import queue
from unittest import TestCase

from mcpager.client import Session, MCPClient
from mcpager.adapters import LangGraphBackend


class MockTransport:
    """Simulated transport that echoes specific responses."""

    def __init__(self):
        self.sent_messages = []
        self.responses = queue.Queue()

    def send(self, message: dict):
        self.sent_messages.append(message)
        method = message["method"]

        # Simulate backend responses:
        if method == "initialize":
            self.responses.put({"id": message["id"], "result": {"version": "1.0"}})
        elif method == "tools/list":
            self.responses.put({
                "id": message["id"],
                "result": [{"name": "echo", "description": "Echoes text"}],
            })
        elif method == "tools/call":
            args = message["params"]["arguments"]
            self.responses.put({"id": message["id"], "result": {"echo": args}})
        else:
            self.responses.put({"id": message["id"], "error": f"Unknown method {method}"})

    def receive(self, timeout = None):
        try:
            return self.responses.get(timeout=timeout or 1)
        except queue.Empty:
            return None
        

class TestClient(TestCase):
    
    def setUp(self):
        transport = MockTransport()
        session = Session(transport)
        backend = LangGraphBackend()
        self.client = MCPClient(backend, session)

    def test_initialize(self):
        info = self.client.initialize()
        self.assertEqual(info['version'], '1.0')

    def test_list_tools(self):
        tools = self.client.list_tools()
        self.assertEqual(tools[0]['name'], 'echo')

    def test_call_tool(self):
        result = self.client.call_tool("echo", {"text": "hello world"})
        self.assertEqual(result['echo']['text'], 'hello world')
