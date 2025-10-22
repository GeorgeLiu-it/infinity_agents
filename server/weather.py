# math_server.py
# weather_server.py
"""
SSE server: we can deploy them everywhere we want, e.g. deploy in the enterprise cloud.
"""
import subprocess
from typing import List
from mcp.server.fastmcp import FastMCP
import aiohttp
import os
import asyncio
import logging

from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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
    """Get the MCP welcome information from remote server.
    """
    print("This is a log from the SSE server")
    return "Welcome to Remote MCP Server!!!"

# Get the current weather information from OpenWeatherMap
@mcp.tool()
async def get_remote_cmp_weather_from_OpenWeatherMap(location: str) -> str:
    """
    Get information from OpenWeatherMap.
    Get real-time weather information for a given location using the OpenWeatherMap API.

    ---
    🧩 **Tool Context**
    This function is designed to be registered as an MCP (Model Context Protocol) tool.
    That means it can be dynamically discovered and called by an LLM or an agent runtime
    (for example, to answer questions like "What’s the weather in London?").

    ---
    📥 **Parameters**
    - `location` (str): The name of the city or region to query (e.g. `"London"`, `"Beijing"`).
    """
    logger.info(f"get_weather tool invoked for location: {location}")
    
    try:
        # Use OpenWeatherMap API, you need to register and get an API key
        # Read API key from environment variable
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return "Error: OpenWeatherMap API key not found. Please set OPENWEATHER_API_KEY environment variable."
        
        # Build API request URL
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': location,
            'appid': api_key,
            'units': 'metric',  # Use Celsius
            'lang': 'en'        # English description
        }
        
        logger.debug(f"Fetching weather data for: {location}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse weather data
                    city = data.get('name', location)
                    country = data.get('sys', {}).get('country', '')
                    temp = data['main']['temp']
                    feels_like = data['main']['feels_like']
                    humidity = data['main']['humidity']
                    description = data['weather'][0]['description']
                    wind_speed = data['wind']['speed']
                    
                    weather_data = (
                        f"Weather in {city}, {country}:\n"
                        f"🌡️ Temperature: {temp}°C (Feels like {feels_like}°C)\n"
                        f"☁️ Conditions: {description}\n"
                        f"💧 Humidity: {humidity}%\n"
                        f"🌬️ Wind Speed: {wind_speed} m/s"
                    )
                    
                    logger.info(f"Weather data retrieved for {location}")
                    return weather_data
                    
                elif response.status == 404:
                    return f"Error: Location '{location}' not found. Please check the spelling."
                else:
                    error_text = await response.text()
                    logger.error(f"Weather API error: {response.status} - {error_text}")
                    return f"Error getting weather information: HTTP {response.status}"
                    
    except aiohttp.ClientError as e:
        logger.error(f"Network error in get_weather for {location}: {e}")
        return f"Network error: Unable to connect to weather service - {str(e)}"
    except Exception as e:
        logger.error(f"Error in get_weather for {location}: {e}")
        return f"Error getting weather for {location}: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="sse")