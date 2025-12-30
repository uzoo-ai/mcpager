from typing import List

from mcpager.adapters import BackendAdapter
from .session import Session


class MCPClient:
    """User-facing high-level client for interacting with a backend."""

    def __init__(self, backend: BackendAdapter, session: Session):
        self.backend = backend
        self.session = session

    def initialize(self, **kwargs) -> dict:
        return self.backend.initialize(self.session, **kwargs)

    def list_tools(self) -> List[dict]:
        return self.backend.list_tools(self.session)

    def call_tool(self, name: str, **kwargs: dict) -> dict:
        return self.backend.call_tool(self.session, name, **kwargs)