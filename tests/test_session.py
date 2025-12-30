from unittest import TestCase

from mcpager.client import Session

class TestSession(TestCase):

    def test_basic_session(self):
        session = Session.from_command("python", ["tests/mock_server.py"])
        print("Initializing session...")
        info = session.initialize()
        print("Initialization result:", info)

        print("Listing tools...")
        tools = session.list_tools()
        print("Tools:", tools)

        self.assertIsInstance(tools, list)
        self.assertTrue(any(t["name"] == "echo" for t in tools))
        session.close()
