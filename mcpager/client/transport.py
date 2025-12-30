import json
import subprocess
import time
import abc
from typing import Any, Optional

import requests


class Transport(abc.ABC):
    """Abstract transport interface for MCP communication."""

    @abc.abstractmethod
    def send(self, message: dict[str, Any]) -> None:
        """Send a JSON-RPC message to the backend."""
        raise NotImplementedError

    @abc.abstractmethod
    def receive(self, timeout: Optional[float] = None) -> dict[str, Any]:
        """Wait for a JSON-RPC message from the backend."""
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        """Cleanly close the connection."""
        raise NotImplementedError



class StdioTransport(Transport):
    def __init__(self, command: list[str]):
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def send(self, message: dict[str, Any]):
        line = json.dumps(message)
        print(message)
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()

    def receive(self, timeout: float = 10.0) -> dict[str, Any]:
        """
        Read a single JSON message from stdout, blocking up to `timeout` seconds.
        """
        start = time.time()
        buffer = ""

        while True:
            # Check timeout
            if time.time() - start > timeout:
                raise TimeoutError("Timed out waiting for server response.")

            # Try to read a single character (non-blocking when no data)
            char = self.process.stdout.read(1)
            if char:
                buffer += char
                if char == "\n":  # End of message line
                    line = buffer.strip()
                    if not line:
                        buffer = ""
                        continue
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError as e:
                        raise RuntimeError(f"Invalid JSON line: {line!r}") from e
            else:
                # Sleep a bit to avoid busy waiting
                time.sleep(0.01)

    def close(self):
        """Gracefully terminate the subprocess."""
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()


def event_stream(response):
    response.encoding = 'utf-8'
    for chunk in response.iter_lines(decode_unicode=True):
        if not chunk:
            continue
        if chunk.startswith("data:"):
            data_str = chunk[len("data:"):].strip()
            try:
                data = json.loads(data_str)
                yield data
            except json.JSONDecodeError:
                print(f"[WARN] Skipping invalid JSON chunk: {data_str}")


class HttpTransport(Transport):
    """Simple synchronous HTTP transport for JSON-RPC 2.0."""

    def __init__(self, base_url: str, headers: Optional[dict[str, str]] = None, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {
            "Content-Type": "application/json"
        }
        self.timeout = timeout

    def send(self, message: dict[str, Any]) -> None:
        """Store outgoing message (used by Session._send_request)."""
        self._last_message = message

    def receive(self, timeout: Optional[float] = None) -> dict[str, Any]:
        """Send stored request and wait for a response."""
        if not hasattr(self, "_last_message"):
            raise RuntimeError("No message to send. Call send() first.")

        payload = self._last_message
        del self._last_message

        try:
            resp = requests.post(
                self.base_url,
                json=payload,
                headers={
                    **self.headers,
                    **{"Accept": "application/json, text/event-stream"}
                },
                timeout=timeout or self.timeout,
            )
            if resp.headers.get('mcp-session-id'):
                self.headers.setdefault('mcp-session-id', resp.headers['mcp-session-id'])
        except Exception as e:
            raise RuntimeError(f"HTTP request failed: {e}")

        if resp.status_code != 200:
            raise RuntimeError(f"HTTP error {resp.status_code}: {resp.text}")

        try:
            content_type = resp.headers.get("Content-Type", "")
            # --- Handle Server-Sent Events (text/event-stream) ---
            if "text/event-stream" in content_type:
                return event_stream(resp)
            # --- Handle regular JSON response ---
            else:
                data = resp.json()
        except ValueError:
            raise RuntimeError(f"Invalid JSON response: {resp.text}")
        finally:
            resp.close()

        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected response type: {type(data)}")

        if "error" in data:
            raise RuntimeError(f"Server error: {data['error']}")

        return data.get("result", {})

    def close(self) -> None:
        """No persistent connection to close."""
        pass
