import requests
from flask import Flask, request, render_template, redirect, url_for, session
from datetime import datetime, timedelta, timezone

# Flask App Configuration
app = Flask(__name__)
app.secret_key = 'hudacantik'
app.permanent_session_lifetime = timedelta(days=1)

# OpenWeatherMap API Configuration
API_KEY = "983655faaf7a248ff79c38cedf788712"
CURRENT_WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
HOURLY_FORECAST_API_URL = "https://pro.openweathermap.org/data/2.5/forecast/hourly"

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        location = request.form.get('cityName')
        if location:
            session['location'] = location
        else:
            return render_template('index.html', error="Please provide a valid location.")

    location = session.get('location')
    if not location:
        return redirect(url_for('index'))  # Redirect to index if no location is set

    querystring = {
        "q": location,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        # Fetch current weather data
        current_response = requests.get(CURRENT_WEATHER_API_URL, params=querystring)
        current_response.raise_for_status()
        current_data = current_response.json()

        # Check if the response is valid
        if current_data.get('cod') != 200:
            return render_template('index.html', error="Invalid city name or API error.")

        # Parse current weather data
        readable_date = datetime.fromtimestamp(current_data['dt'], timezone.utc).strftime('%A, %d/%m/%Y')
        readable_day = datetime.fromtimestamp(current_data['dt'], timezone.utc).strftime('%A')

        # Fetch hourly forecast data
        hourly_response = requests.get(HOURLY_FORECAST_API_URL, params=querystring)
        hourly_response.raise_for_status()
        hourly_data = hourly_response.json().get('list', [])

        # Parse hourly forecast data
        hourly_weather = [
            {
                "time": datetime.fromtimestamp(hour['dt'], timezone.utc).strftime('%H:%M'),
                "temp": hour['main']['temp'],
                "description": hour['weather'][0]['description'],
                "icon": f"http://openweathermap.org/img/wn/{hour['weather'][0]['icon']}@2x.png"
            }
            for hour in hourly_data[:12]  # Get the first 12 hours
        ]

        # Prepare the weather data for rendering
        weather_data = {
            "name": current_data['name'],
            "day": readable_day,
            "date": readable_date,
            "temp_c": current_data['main']['temp'],  # Celsius
            "temp_f": (current_data['main']['temp'] * 9/5) + 32,  # Fahrenheit
            "description": current_data['weather'][0]['description'],
            "icon": f"http://openweathermap.org/img/wn/{current_data['weather'][0]['icon']}@2x.png",
            "hourly": hourly_weather
        }

        return render_template('index.html', weather=weather_data)

    except requests.exceptions.RequestException:
        return render_template('index.html', error="Failed to connect to the weather service.")
