import requests


def get_weather():
    """Fetch current weather information."""
    city = "New York"  # You can modify this to accept dynamic input
    api_key = "YOUR_API_KEY"  # Use a real API key from OpenWeatherMap or similar
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"

    try:
        response = requests.get(url)
        data = response.json()
        if "current" in data:
            return f"The current temperature in {city} is {data['current']['temp_c']}°C with {data['current']['condition']['text']}."
        else:
            return "Sorry, I couldn't fetch the weather at the moment."
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"
