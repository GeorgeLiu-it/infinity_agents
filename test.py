import asyncio
import logging
import os
import aiohttp
from dotenv import load_dotenv

# === Logging setup ===
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
# Load environment variables
load_dotenv()

# === Weather Tool ===
async def get_weather(location: str) -> str:
    """Get real-time weather information for a location using OpenWeatherMap API."""
    logger.info(f"get_weather tool invoked for location: {location}")
    
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        logger.error("Missing OpenWeatherMap API key.")
        return "Error: Missing API key for weather service. Please set OPENWEATHER_API_KEY."

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": api_key,
            "units": "metric",   # Celsius
            "lang": "zh_cn"      # Chinese description
        }

        logger.debug(f"Sending request to OpenWeatherMap for {location}: {url} {params}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Weather API request failed: {response.status}, {text}")
                    return f"Error: Unable to fetch weather for {location}. (HTTP {response.status})"

                data = await response.json()
                logger.debug(f"Weather data received for {location}: {data}")

                # Parse the returned data
                weather_main = data["weather"][0]["description"]
                temp = data["main"]["temp"]
                humidity = data["main"]["humidity"]
                wind_speed = data["wind"]["speed"]

                weather_info = (
                    f"当前{location}天气：{weather_main}，气温 {temp}°C，"
                    f"湿度 {humidity}% ，风速 {wind_speed} m/s。"
                )

                logger.info(f"Weather data retrieved successfully for {location}")
                return weather_info

    except Exception as e:
        logger.exception(f"Error in get_weather for {location}: {e}")
        return f"Error getting weather for {location}: {str(e)}"


# === Main function for CLI testing ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python get_weather.py <location>")
        sys.exit(1)

    location = " ".join(sys.argv[1:])
    print(f"Fetching weather for: {location}")

    # Run the async function in main
    result = asyncio.run(get_weather(location))
    print(result)
