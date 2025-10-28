"""
SSE Weather MCP Server
Enhanced with detailed trace logging (console-only output)
"""

import subprocess
from typing import List
from mcp.server.fastmcp import FastMCP
import aiohttp
import os
import asyncio
import logging
from dotenv import load_dotenv

# -------------------------------------------------------------
# Logging Setup (console only)
# -------------------------------------------------------------
logger = logging.getLogger("WeatherMCP")
logger.setLevel(logging.DEBUG)  # Capture everything (DEBUG and up)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)

# Ensure no duplicate handlers
if not logger.hasHandlers():
    logger.addHandler(console_handler)
else:
    logger.handlers.clear()
    logger.addHandler(console_handler)

# Disable propagation to root logger
logger.propagate = False

# -------------------------------------------------------------
# Load environment variables
# -------------------------------------------------------------
load_dotenv()

# Initialize MCP server
mcp = FastMCP("Weather")


# -------------------------------------------------------------
# Tool: System Info
# -------------------------------------------------------------
@mcp.tool()
def system_info() -> str:
    """
    Get system information for local server like: CPU usage, memory usage, and disk usage.
    """
    logger.debug("[system_info] Invoked.")
    try:
        cpu_info = subprocess.check_output("top -bn1 | grep 'Cpu(s)'", shell=True, text=True).strip()
        mem_info = subprocess.check_output("free -h", shell=True, text=True).strip()
        disk_info = subprocess.check_output("df -h", shell=True, text=True).strip()

        result = f"CPU Info:\n{cpu_info}\n\nMemory Info:\n{mem_info}\n\nDisk Info:\n{disk_info}"
        logger.debug("[system_info] Successfully gathered system info.")
        return result

    except subprocess.CalledProcessError as e:
        logger.error(f"[system_info] Error fetching system info: {e}")
        return f"Error fetching system info: {e}"


# -------------------------------------------------------------
# Tool: Remote MCP Welcome
# -------------------------------------------------------------
@mcp.tool()
async def get_local_mcp_welcome(location: str) -> str:
    """
    Get the MCP welcome information from remote server.
    """
    logger.debug(f"[get_remote_mcp_welcome] Invoked with location='{location}'.")
    print("This is a log from the SSE server")
    logger.debug("[get_remote_mcp_welcome] Returning welcome message.")
    return "Welcome to Remote MCP Server!!!"


# -------------------------------------------------------------
# Tool: Weather from OpenWeatherMap
# -------------------------------------------------------------
@mcp.tool()
async def get_local_mcp_weather_from_OpenWeatherMap(location: str) -> str:
    """
    Get information from OpenWeatherMap.
    Get real-time weather information for a given location using the OpenWeatherMap API.
    `location (str)`: The name of the city or region to query (e.g. "London", "Beijing")
    """
    logger.debug(f"[get_remote_cmp_weather_from_OpenWeatherMap] Invoked with location='{location}'.")

    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            logger.warning("[get_remote_cmp_weather_from_OpenWeatherMap] API key missing.")
            return "Error: OpenWeatherMap API key not found. Please set OPENWEATHER_API_KEY."

        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": api_key,
            "units": "metric",
            "lang": "en",
        }

        logger.debug(f"[get_remote_cmp_weather_from_OpenWeatherMap] Request params: {params}")

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                logger.debug(f"[get_remote_cmp_weather_from_OpenWeatherMap] HTTP status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"[get_remote_cmp_weather_from_OpenWeatherMap] Data received: {data}")

                    city = data.get("name", location)
                    country = data.get("sys", {}).get("country", "")
                    temp = data["main"]["temp"]
                    feels_like = data["main"]["feels_like"]
                    humidity = data["main"]["humidity"]
                    description = data["weather"][0]["description"]
                    wind_speed = data["wind"]["speed"]

                    weather_data = (
                        f"Weather in {city}, {country}:\n"
                        f"🌡️ Temperature: {temp}°C (Feels like {feels_like}°C)\n"
                        f"☁️ Conditions: {description}\n"
                        f"💧 Humidity: {humidity}%\n"
                        f"🌬️ Wind Speed: {wind_speed} m/s"
                    )

                    logger.info(f"[get_remote_cmp_weather_from_OpenWeatherMap] Weather data retrieved for {location}.")
                    return weather_data

                elif response.status == 404:
                    logger.warning(f"[get_remote_cmp_weather_from_OpenWeatherMap] Location '{location}' not found.")
                    return f"Error: Location '{location}' not found."
                else:
                    error_text = await response.text()
                    logger.error(f"[get_remote_cmp_weather_from_OpenWeatherMap] HTTP {response.status} - {error_text}")
                    return f"Error getting weather information: HTTP {response.status}"

    except aiohttp.ClientError as e:
        logger.error(f"[get_remote_cmp_weather_from_OpenWeatherMap] Network error: {e}")
        return f"Network error: Unable to connect to weather service - {str(e)}"

    except Exception as e:
        logger.exception(f"[get_remote_cmp_weather_from_OpenWeatherMap] Unexpected error: {e}")
        return f"Error getting weather for {location}: {str(e)}"

# -------------------------------------------------------------
# Main entry
# -------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting Weather MCP Server (transport=SSE)...")
    mcp.run(transport="sse")