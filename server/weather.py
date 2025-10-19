# math_server.py
# weather_server.py
"""
SSE server: we can deploy them everywhere we want, e.g. deploy in the enterprise cloud.
"""
import subprocess
from typing import List
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather")

# Get the current system usage
@mcp.tool()
def system_info() -> str:
    """
    Return basic system information: CPU usage, memory usage, and disk usage.
    """
    try:
        # CPU info
        cpu_info = subprocess.check_output("top -bn1 | grep 'Cpu(s)'", shell=True, text=True).strip()

        # Memory info
        mem_info = subprocess.check_output("free -h", shell=True, text=True).strip()

        # Disk info
        disk_info = subprocess.check_output("df -h", shell=True, text=True).strip()

        # Combine results
        result = f"CPU Info:\n{cpu_info}\n\nMemory Info:\n{mem_info}\n\nDisk Info:\n{disk_info}"
        return result

    except subprocess.CalledProcessError as e:
        return f"Error fetching system info: {e}"

@mcp.tool()
async def get_remote_mcp_welcome(location: str) -> str:
    """Get the MCP welcome information from remote server."""
    print("This is a log from the SSE server")
    return "Welcome to Remote MCP Server!!!"

if __name__ == "__main__":
    mcp.run(transport="sse")