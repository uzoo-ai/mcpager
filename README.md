# MCPager 📟  
*A lightweight synchronous client for Model Context Protocol (MCP) servers*

MCPager is a small, fast, and predictable Python client for interacting with **Model Context Protocol (MCP)** servers.  
It is designed for **independent AI developers** who want to connect tools, agents, and LLMs to MCP backends without asyncio, event loops, or framework lock-in.

MCPager acts like a **pager**: it sends a request, waits for a response, and delivers it reliably — whether the MCP server is running over **stdio**, **HTTP**, or **streaming (SSE)**.

---

## Why MCPager?

Most MCP client libraries today are:
- deeply async,
- tightly coupled to one agentic framework, if any (e.g. LangChain),
- or built around complex lifecycle management.

MCPager takes a different approach:

**Simple. Synchronous. Composable.**

- No `asyncio`
- No background event loops
- Provides abstract adapter for an agentic implementation of your choice (although a concrete LangChain adapter also available out of the box)
- Designed for **tool-calling agents**

---

## Features

- 🧠 **Session-based MCP protocol**
- 🔌 **Multiple transports**
  - `stdio` (local processes)
  - `http` (FastMCP, remote servers)
  - `text/event-stream` (SSE / streaming MCP)
- 🧰 **Tool discovery & invocation**
- 🧩 **LangGraph & LangChain integration**
- 🧵 Thread-safe synchronous request handling
- 🔍 Built-in JSON-RPC and session ID management

---

## Installation

```bash
pip install mcpager
```

## Quick Example
1. Start an MCP server

For example, using FastMCP:

```bash
fastmcp serve examples/echo_server.py --transport http
```

2. Connect using MCPager

```python
from mcpager.transports import StdioTransport, HttpTransport
from mcpager.session import Session
from mcpager.backends import LangGraphBackend
from mcpager.client import MCPClient

transport = HttpTransport('http://localhost:8000/mcp')
# or you can use StdioTransport for local testing like this:
# transport = StdioTransport(["fastmcp", "run", "echo_server.py"])
session = Session(transport)
backend = LangGraphBackend()
client = MCPClient(backend, session)

client.initialize()

tools = client.list_tools()
print(tools)

result = client.call_tool("echo", text="Hello from MCPager!")
print(result)
```

## Using MCPager with LangGraph

MCPager can expose MCP tools directly to LangGraph agents.

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from mcpager.langgraph import load_mcp_tools

llm = ChatOpenAI(model="gpt-4o-mini")
tools = load_mcp_tools(client)

agent = create_react_agent(llm, tools)

result = agent.invoke({"messages": [("human", "Echo: MCP is working!")]})
print(result)
```
Your MCP tools are now callable by the agent as native LangGraph tools.

## Architecture

MCPager is built around three simple layers:

```scss
MCPClient
   ↓
BackendAdapter (LangGraphBackend, etc.)
   ↓
Session (JSON-RPC + session handling)
   ↓
Transport (stdio, http, SSE)
```

This makes MCPager:

- easy to test

- easy to extend

- safe to embed in agents, workers, or pipelines


## Transports

Stdio (local MCP servers)
```python
StdioTransport(["python", "my_server.py"])
```

HTTP (FastMCP or remote MCP)
```python
HttpTransport("http://localhost:3000")
```
Supports:

- normal JSON responses

- text/event-stream (SSE streaming)

## Documentation

Full documentation and guides are available here:

👉 https://uzoo.ai/agents/mcp

This includes:

- MCP protocol overview

- Tool schemas

- Server & client examples

- Agent integration patterns

## Who is MCPager for?

MCPager is for:

- Independent AI developers

- Agent builders

- Tool & plugin authors

- Anyone building MCP-based systems without wanting async complexity

If you want reliable tool calls from LLM agents to real backends, MCPager is built for you.

## Project Philosophy

MCPager follows a few strict principles:

- Synchronous by default

- Explicit session handling

- No hidden magic

- Transport-agnostic

- Agent-friendly

Think of it as:

> “The curl of MCP.”

## License

Apache 2.0

## Contributions

PRs, issues, and ideas are welcome.
MCPager is meant to grow with the MCP ecosystem. 📟

Below is our current backlog:

---
- Task: support sampling
- Task: support elicitation
- **30.12.2025** MCPager client released!