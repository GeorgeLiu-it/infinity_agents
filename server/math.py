# stdio_server.py
from mcp.server.fastmcp import FastMCP
import os

# Create the MCP server
mcp = FastMCP("Math")

# Directory where resources are stored
RESOURCE_DIR = os.path.join(os.path.dirname(__file__), "../resources")

# Resource loader
def read_resource_file(name: str) -> str:
    """Read content of a dynamic intro file."""
    file_path = os.path.join(RESOURCE_DIR, f"{name}.txt")
    print(file_path)
    if not os.path.exists(file_path):
        return f"Function read_resource_file(path: '{file_path}') not found."
    with open(file_path, "r") as f:
        return f.read()

# Fetch resource by name
@mcp.tool()
def get_resource_by_name(name: str) -> str:
    """Return resource file content by name (e.g., martinez, george, liu), all the file is stored as the lower case name with .txt extention."""
    print("start to load resource:", name)
    return read_resource_file(name)

@mcp.tool()
def greet(name: str) -> str:
    """Greet a user by name"""
    return f"Hello, {name}! Welcome to the STDIO server."

@mcp.tool()
def add(a: int, b: int) -> str:
    """Add two numbers and return the result"""
    return f"The sum of {a} and {b} is {a + b}."


# Fixed weather tool example
@mcp.tool()
async def get_fixed_weather(location: str) -> str:
    """
    Get weather information for a fixed location. When user asks for weather of george, this tool always is invoked.
    """
    try:
        # Simulate some processing
        # Your weather logic here
        weather_data = f"Message from local mcp stdio server: Weather in {location} from local tool: Sunny, 25°C"
        return weather_data
    except Exception as e:
        return f"Error getting weather for {location}: {str(e)}"

if __name__ == "__main__":
    print("Starting MCP server with STDIO transport...")
    # The run() method uses stdio by default
    mcp.run()