"""
SSE server: we can deploy them everywhere we want, e.g. deploy in the enterprise cloud.
"""
import subprocess
import logging
from typing import List
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('remote_mcp_server.log'),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

logger = logging.getLogger("remote_mcp")

# Changed server name to remote_mcp
mcp = FastMCP("remote_mcp", host="0.0.0.0", port=8000)

# Get the current system usage
@mcp.tool()
def system_info() -> str:
    """
    Return basic system information: CPU usage, memory usage, and disk usage.
    """
    logger.info("system_info tool called")
    try:
        # CPU info
        cpu_info = subprocess.check_output("top -bn1 | grep 'Cpu(s)'", shell=True, text=True).strip()
        logger.debug("CPU info fetched successfully")

        # Memory info
        mem_info = subprocess.check_output("free -h", shell=True, text=True).strip()
        logger.debug("Memory info fetched successfully")

        # Disk info
        disk_info = subprocess.check_output("df -h", shell=True, text=True).strip()
        logger.debug("Disk info fetched successfully")

        # Combine results
        result = f"CPU Info:\n{cpu_info}\n\nMemory Info:\n{mem_info}\n\nDisk Info:\n{disk_info}"
        logger.info("system_info tool completed successfully")
        return result

    except subprocess.CalledProcessError as e:
        logger.error(f"Error fetching system info: {e}")
        return f"Error fetching system info: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in system_info: {e}")
        return f"Unexpected error: {e}"

@mcp.tool()
async def get_remote_mcp_welcome(location: str) -> str:
    """Get the MCP welcome information from remote server."""
    logger.info(f"get_remote_mcp_welcome called with location: {location}")
    print("This is a log from the SSE server")
    
    # Log additional information
    logger.debug(f"Processing welcome message for location: {location}")
    
    result = "Welcome to Remote MCP Server!!!"
    logger.info(f"get_remote_mcp_welcome completed, returning: {result}")
    return result

# Add a tool with detailed logging
@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather information for a location."""
    logger.info(f"get_weather tool invoked for location: {location}")
    
    try:
        # Simulate some processing
        logger.debug(f"Processing weather request for: {location}")
        
        # Your weather logic here
        weather_data = f"Weather in {location}: Sunny, 25°C"
        
        logger.info(f"Weather data retrieved for {location}: {weather_data}")
        return weather_data
        
    except Exception as e:
        logger.error(f"Error in get_weather for {location}: {e}")
        return f"Error getting weather for {location}: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting Remote MCP Server on port 8000")
    try:
        import inspect
        print(inspect.signature(mcp.run))
        mcp.run(transport="sse")
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise