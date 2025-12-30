from abc import ABC, abstractmethod
from typing import List, Any, Dict
from functools import partial

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import create_model

from mcpager.client import Session


class BackendAdapter(ABC):
    """Abstract interface defining how to talk to a backend engine."""

    @abstractmethod
    def initialize(self, session: Session, **kwargs) -> dict:
        pass

    @abstractmethod
    def list_tools(self, session: Session) -> List[dict]:
        pass

    @abstractmethod
    def call_tool(self, session: Session, name: str, args: dict) -> dict:
        pass


class LangGraphBackend(BackendAdapter):
    """Implements backend logic for a LangGraph-style MCP server."""

    def initialize(self, session: Session, **kwargs) -> dict:
        return session.initialize(**kwargs)

    def list_tools(self, session: Session) -> List[BaseTool]:
        tools_data = session.list_tools()
        return [
            self.convert_mcp_tool_to_langchain_tool(session, t)
            for t in tools_data
        ]

    def call_tool(self, session: Session, name: str, **kwargs: Dict[str, Any]) -> Any:
        result = session._send_request("tools/call", {"name": name, "arguments": kwargs})
        # Return as (content, artifact)
        # 'content' is what the LLM sees, 'artifact' is the raw result
        if isinstance(result, dict):
            content = result.get("content") or result.get("result") or str(result)
        else:
            content = str(result)

        return (content, result)
    
    def convert_mcp_tool_to_langchain_tool(
            self,
            session: Session,
            tool_info: dict
        ) -> StructuredTool:
        """
        Convert an MCP tool description (from session.list_tools()) into
        a LangChain-compatible StructuredTool
        """

        tool_name = tool_info["name"]
        description = tool_info.get("description", "")

        # Build args schema dynamically from MCP input schema (if any)
        input_schema = tool_info.get("inputSchema", {"type": "object", "properties": {}})
        properties = input_schema.get("properties", {})

        fields = {}
        for name, prop in properties.items():
            typ = str  # default type
            match prop.get("type"): 
                case "number":
                    typ = float
                case "integer":
                    typ = int
                case "boolean":
                    typ = bool
                case "array":
                    typ = list
            fields[name] = (typ, ... if name in input_schema.get("required", []) else None)

        ArgsModel = create_model(f"{tool_name}_Args", **fields)

        return StructuredTool(
            name=tool_name,
            description=description,
            args_schema=ArgsModel,
            func=partial(self.call_tool, session, tool_name),
            response_format="content_and_artifact",
        )
