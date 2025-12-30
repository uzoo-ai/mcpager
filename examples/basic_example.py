from typing import List
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
from dotenv import load_dotenv

from mcpager.client import MCPClient, Session, SessionError, MCPClient, StdioTransport, HttpTransport
from mcpager.adapters import LangGraphBackend

load_dotenv()


def build_langgraph_agent(client: MCPClient):
    """
    Build a LangGraph ReAct agent that uses tools exposed by an MCP server
    through the provided MCPClient.
    """

    # 1. Initialize the MCP session (handshake)
    client.initialize()

    # 2. Fetch tool specifications from the MCP server
    tools: List[StructuredTool] = client.list_tools()

    # 4. Create an LLM
    llm = ChatOpenAI(model="gpt-5-mini")

    # 5. Build and return the LangGraph ReAct agent
    agent = create_react_agent(llm, tools)

    return agent



# ==============================================================
# Run the client
# ==============================================================

if __name__ == "__main__":
    transport = StdioTransport(["fastmcp", "run", "echo_server.py"])
    # transport = HttpTransport('http://localhost:8000/mcp')
    session = Session(transport)
    backend = LangGraphBackend()
    client = MCPClient(backend, session)

    try:
        print("Initializing...")
        print(client.initialize(
            capabilities={
                "roots": {
                    "listChanged": True
                },
                "sampling": {}
            }
        ))

        print("Listing tools...")
        tools = client.list_tools()
        for t in tools:
            print(f"- {t.name}: {t.description}")
            print("Args schema:", t.args_schema.schema())

        print("Calling echo...")
        result = tools[0].invoke({"text": "Hello from LangGraph!"})
        print("Result:", result)

        # Build LangGraph agent from MCPClient
        agent = build_langgraph_agent(client)

        # Run an example query
        response = agent.invoke(
            {
                'messages': [
                    {
                        'role': 'user',
                        'content': "Please echo the text 'Hello from MCPClient!'"
                    }
                ]
            }
        )

        print("Agent response:", response)

    except SessionError as e:
        print("SessionError:", e)
    finally:
        transport.close()
