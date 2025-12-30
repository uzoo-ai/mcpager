import time
import threading
import uuid
from typing import Any, Dict, Optional
from .transport import Transport


class SessionError(Exception):
    """Base class for all session errors."""
    pass


class Session:
    """
    A synchronous implementation of an MCP client session.
    Mirrors the logic of async ClientSession.initialize() and list_tools().
    """

    def __init__(self, transport: Transport):
        self.transport = transport
        self._lock = threading.Lock()
        self._id_counter = 0
        self.capabilities = {}
        self.initialized = False

    def _next_id(self) -> str:
        self._id_counter += 1
        return f"req-{self._id_counter}-{uuid.uuid4().hex[:6]}"

    def _send_request(
        self,
        method: str,
        params: Optional[dict] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """Send a request and wait for the corresponding response.

        Supports both normal and streaming transports.
        """
        with self._lock:
            req_id = self._next_id()
            message = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
                "params": params or {},
            }

            self.transport.send(message)

            response = self.transport.receive(timeout=timeout)

            # normal dict response
            if isinstance(response, dict):
                if response.get("id") == req_id:
                    if "error" in response:
                        raise SessionError(response["error"])
                    return response.get("result", {})
                else:
                    raise SessionError(f"Unexpected response id: {response.get('id')}")

            # streaming generator
            elif hasattr(response, "__iter__"):
                final_result = None
                for event in response:
                    if not isinstance(event, dict):
                        continue

                    # Optional: handle progress events or updates
                    if event.get("method") == "progress":
                        # You could yield or log this
                        continue

                    # Handle final result
                    if event.get("id") == req_id:
                        if "error" in event:
                            raise SessionError(event["error"])
                        final_result = event.get("result")

                if final_result is None:
                    raise SessionError(f"No final result for request {req_id}")
                return final_result

            else:
                raise SessionError(f"Unexpected response type: {type(response)}")


    # === MCP client methods ===

    def initialize(
            self,
            client_name: str = "mcpager",
            client_version: str = "0.1.0",
            protocol_version: str = "2025-03-26",
            capabilities: Optional[str] = None
        ):
        """Initialize connection to the MCP server."""
        params = {
            "clientInfo": {
                "name": client_name,
                "version": client_version,
            },
            "capabilities": capabilities or {},
            "protocolVersion": protocol_version
        }

        result = self._send_request("initialize", params)
        self.capabilities = result.get("capabilities", {})
        self.session_id = result.get("sessionId")
        self.initialized = True
        return result

    def list_tools(self):
        """Retrieve list of tools available on the MCP server."""
        if not self.initialized:
            raise SessionError("Session not initialized. Call initialize() first.")

        result = self._send_request("tools/list")
        tools = result.get("tools", [])
        return tools

    def close(self):
        """Gracefully close the transport connection."""
        try:
            self.transport.close()
        except Exception:
            pass
