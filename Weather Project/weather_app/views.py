import requests
import datetime
from django.shortcuts import render
from datetime import datetime as dt

# Function to fetch weather alerts from weather.gov
def get_weather_alerts(latitude, longitude, timestamp):
    base_url = "https://api.weather.gov/alerts/active"
    params = {
        "point": f"{latitude},{longitude}"
    }
    headers = {
        "User-Agent": "weather_checker/1.0 (gurufox.ai)",
        "Accept": "application/geo+json"
    }
    response = requests.get(base_url, headers=headers, params=params)
    data = response.json()
    alerts = data.get('features', [])

    # Extract only the summary information
    summaries = []
    for alert in alerts:
        properties = alert.get('properties', {})
        summary = properties.get('headline', 'No headline available')
        summaries.append(summary)
    
    return summaries

# Function to generate custom messages based on weather description
def get_custom_message(description):
    description = description.lower()  # Convert to lowercase for comparison
    if "sunny" in description:
        return "It's going to be a bright and sunny day! Don't forget to bring sunscreen, stay hydrated, and wear sunglasses."
    elif "clear sky" in description:
        return "Hey, clear sky ahead! Don't forget to wear classy clothes and sunglasses!"
    elif "overcast clouds" in description:
        return "Cloudy weather ahead. Wear comfortable layers and bring a light jacket in case it gets chilly."
    elif "rain" in description or "showers" in description:
        return "Rain on the way. Don't forget to bring an umbrella."
    elif "flood" in description:
        return "Flooding expected. Avoid low-lying areas and stay safe. Check local advisories for evacuation routes."
    elif "snowy" in description:
        return "Snowy conditions ahead. Dress warmly, and be cautious on the roads. Consider postponing travel if possible."
    elif "windy" in description:
        return "Windy weather ahead. Secure any loose items outside and be careful when driving, especially high-profile vehicles."
    else:
        return ""

# Function to fetch weather data and forecasts from OpenWeatherMap
def fetch_weather_and_forecast(city, api_key, current_weather_url, forecast_url):
    current_weather_url_formatted = current_weather_url.format(city, api_key)
    response = requests.get(current_weather_url_formatted).json()

    if response.get('cod') != 200:
        raise Exception(f"Error fetching current weather data: {response.get('message', 'No message')}")

    if 'coord' not in response:
        raise Exception(f"'coord' key not found in the current weather response for city: {city}")

    lat, lon = response['coord']['lat'], response['coord']['lon']
    forecast_url_formatted = forecast_url.format(lat, lon, api_key)
    forecast_response = requests.get(forecast_url_formatted).json()

    if forecast_response.get('cod') != '200':
        raise Exception(f"Error fetching forecast data: {forecast_response.get('message', 'No message')}")

    weather_data = {
        'city': city,
        'latitude': lat,
        'longitude': lon,
        'temperature': round((response['main']['temp'] - 273.15) * 9/5 + 32, 2),
        'description': response['weather'][0]['description'],
        'icon': response['weather'][0]['icon'],
    }

    daily_forecasts = []
    for forecast in forecast_response['list']:
        daily_forecasts.append({
            'day': forecast['dt_txt'],
            'min_temp': round((forecast['main']['temp_min'] - 273.15) * 9/5 + 32, 2),
            'max_temp': round((forecast['main']['temp_max'] - 273.15) * 9/5 + 32, 2),
            'description': forecast['weather'][0]['description'],
            'icon': forecast['weather'][0]['icon'],
            'message': get_custom_message(forecast['weather'][0]['description'])
        })

    return weather_data, daily_forecasts

# Main view for the weather app
def index(request):
    api_key = '7e7527e98e67e1a7cbebd8f19783aa5f'
    current_weather_url = 'https://api.openweathermap.org/data/2.5/weather?q={}&appid={}'
    forecast_url = 'https://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&appid={}'

    background = 'background.gif'  # Initialize background variable

    if request.method == 'POST':
        city = request.POST['city']
        date = request.POST['date']
        time = request.POST['time']

        try:
            weather_data, daily_forecasts = fetch_weather_and_forecast(city, api_key, current_weather_url, forecast_url)
            selected_datetime = dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            closest_forecast = None
            min_time_diff = float('inf')
            for forecast in daily_forecasts:
                forecast_datetime = dt.strptime(forecast['day'], "%Y-%m-%d %H:%M:%S")
                time_diff = abs((forecast_datetime - selected_datetime).total_seconds())
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_forecast = forecast

            formatted_time = selected_datetime.strftime("%I:%M %p")
            forecast = {
                'city': city,
                'date': date,
                'time': formatted_time,
                'weather': closest_forecast
            }
            alerts = get_weather_alerts(weather_data['latitude'], weather_data['longitude'], selected_datetime.isoformat())

            # Determine background based on time
            hour = selected_datetime.hour
            background = 'day_background.gif' if 6 <= hour < 18 else 'night_background.gif'

        except Exception as e:
            print(f"Error fetching weather data: {e}")
            forecast, alerts = None, []

        context = {
            'forecast': forecast,
            'alerts': alerts,
            'background': background,
        }
        return render(request, 'weather_app/index.html', context)
    else:
        context = {
            'background': background,
        }
        return render(request, 'weather_app/index.html', context)
