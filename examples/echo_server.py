from fastmcp import FastMCP

mcp = FastMCP("EchoServer")

@mcp.tool()
def echo(text: str) -> str:
    """Echoes the given text back."""
    return text

if __name__ == "__main__":
    mcp.run()
