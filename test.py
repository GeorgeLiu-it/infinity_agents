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

async def get_weather(location: str) -> str:
    """Get real-time weather information for a location."""
    logger.info(f"get_weather tool invoked for location: {location}")
    
    try:
        # Use OpenWeatherMap API, you need to register and get an API key
        # Read API key from environment variable
        # api_key = os.getenv("OPENWEATHER_API_KEY")
        api_key = "a30778ccb6cde56df48816b7dbc83372"
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

async def main():
    """Test function for the weather tool"""
    # Test locations
    test_locations = ["London", "New York", "Tokyo", "Paris"]
    
    for location in test_locations:
        print(f"\n{'='*50}")
        print(f"Testing weather for: {location}")
        print(f"{'='*50}")
        
        result = await get_weather(location)
        print(result)
        
        # Small delay between requests
        await asyncio.sleep(1)

if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("OPENWEATHER_API_KEY"):
        print("ERROR: OPENWEATHER_API_KEY environment variable is not set!")
        print("Please set it first:")
        print("export OPENWEATHER_API_KEY='your_api_key_here'")
    else:
        # Run the test
        asyncio.run(main())