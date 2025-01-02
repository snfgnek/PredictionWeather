import numpy as np
import requests, joblib
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for, session
from datetime import datetime, timedelta, timezone, time
from sklearn.ensemble import RandomForestClassifier
import pytz

# API Configuration
API_KEY = "a9902202138d0bf59b5aae5e0806b2ea"
API_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_API_URL = "https://pro.openweathermap.org/data/2.5/forecast/hourly"

app = Flask(__name__)
app.secret_key = 'hudacantik'
app.permanent_session_lifetime = timedelta(days=1)

#Load model
weather_model = joblib.load('model/predictive_model.sav')

# Ensure weather_model is not a tuple
if isinstance(weather_model, tuple):
    weather_model = weather_model[0]  

@app.route('/clear_session')
def clear_session():
    session.clear()
    return redirect(url_for('index'))

@app.route('/')
def index():
    session.clear()  
    return render_template('index.html', weather=None)

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
        response = requests.get(API_URL, params=querystring)
        response.raise_for_status()
        json_data = response.json()

        # Check if response has valid data
        if json_data.get('cod') != 200:
            return render_template('index.html', error="Invalid city name or API error.")

        # Convert API date timestamp to readable format
        utc = pytz.utc  # Define UTC timezone
        readable_date = datetime.fromtimestamp(json_data['dt'], utc).strftime('%A, %d/%m/%Y')
        readable_day = datetime.fromtimestamp(json_data['dt'], timezone.utc).strftime('%A')

        lat = json_data['coord']['lat']
        lon = json_data['coord']['lon']

        # Fetch forecast data
        forecast_querystring = {
            "q": location,
            "appid": API_KEY,
            "units": "metric"
        }
        forecast_response = requests.get(FORECAST_API_URL, params=forecast_querystring)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json().get('list', [])
        
        local_tz = timezone(timedelta(hours=8))
        current_time = datetime.now(local_tz)
        print("Local Time:", current_time)
        next_full_hour = (current_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        
        hourly_data = [
        {
        "time": datetime.fromtimestamp(hour['dt'], local_tz).strftime('%H:%M'),
        "temp": hour['main']['temp'],
        "description": hour['weather'][0]['description'],
        "icon": f"http://openweathermap.org/img/wn/{hour['weather'][0]['icon']}@2x.png"
        }
        for hour in forecast_data if next_full_hour <= datetime.fromtimestamp(hour['dt'], local_tz) < next_full_hour + timedelta(hours=5)
        ]


        # Prepare the weather data for rendering
        weather_data = {
            "name": json_data['name'],
            "day": readable_day,
            "date": readable_date,
            "lat": json_data['coord']['lat'],
            "lon": json_data['coord']['lon'],
            "temp_c": json_data['main']['temp'],  # Celsius from the API
            "temp_f": (json_data['main']['temp'] * 9/5) + 32,  # Convert Celsius to Fahrenheit
            "feelslike_c": json_data['main']['feels_like'],
            "feelslike_f": (json_data['main']['feels_like'] * 9/5) + 32,  # Convert Celsius to Fahrenheit
            "temp_min": json_data['main']['temp_min'],
            "temp_max": json_data['main']['temp_max'],
            "pressure_mb": json_data['main']['pressure'],
            "humidity": json_data['main']['humidity'],
            "visibility_km": json_data['visibility'] / 1000,  # Convert meters to kilometers
            "visibility_miles": json_data['visibility'] / 1609,  # Convert meters to miles
            "wind_speed_kph": json_data['wind']['speed'] * 3.6,  # Convert m/s to kph
            "wind_speed_mph": json_data['wind']['speed'] * 2.237,  # Convert m/s to mph
            "wind_dir": json_data['wind']['deg'],
            "gust_kph": json_data['wind'].get('gust', 0) * 3.6,  # Convert m/s to kph
            "gust_mph": json_data['wind'].get('gust', 0) * 2.237,  # Convert m/s to mph
            "condition_text": json_data['weather'][0]['description'],
            "condition_icon": f"http://openweathermap.org/img/wn/{json_data['weather'][0]['icon']}@2x.png",
            "rain_1h_mm": json_data.get('rain', {}).get('1h', 0),  # Rain in the last 1 hour (mm)
            "cloud_coverage": json_data['clouds']['all'],  # Cloud coverage percentage
            "country": json_data['sys']['country'],
            "timezone_offset": json_data['timezone'],
            "sunrise": datetime.fromtimestamp(json_data['sys']['sunrise'], timezone.utc).strftime('%H:%M:%S'),
            "sunset": datetime.fromtimestamp(json_data['sys']['sunset'], timezone.utc).strftime('%H:%M:%S'),
            "time": datetime.now().strftime('%H:%M'),
            "hourly": hourly_data
        }

        print(weather_data["hourly"])

        return render_template('index.html', weather=weather_data)
    except requests.exceptions.RequestException as err:
        return render_template('index.html', error="Failed to connect to the weather service.")

@app.route('/day', methods=['GET', 'POST'])
def day():
    # Get the current time in the server's timezone
    current_time = datetime.now().time()
    start_time = time(0, 0)  # 12:00 AM
    end_time = time(18, 59)   # 6:00 PM

    # Check if the current time is within the allowed range
    if not (start_time <= current_time <= end_time):
        return render_template('day.html', weather=None, error="Please click the 'Night' button for night weather information.")
   
    location = session.get('location', None)

    # If the method is POST, update the location from the form
    if request.method == 'POST':
        location = request.form.get('cityName')
        if location:
            session['location'] = location  
        else:
             session.pop('location', None)  # Remove location if empty

    # Handle the case where location is None
    if not location:
        return render_template('day.html', weather=None, error="Please provide a valid location.")
    
    querystring = {
        "q": location,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        # Fetch current weather data
        response = requests.get(API_URL, params=querystring)
        response.raise_for_status()
        json_data = response.json()

        # Check if response has valid data
        if json_data.get('cod') != 200:
            return render_template('day.html', weather=None, error="Invalid city name or API error.")

        # Convert API date timestamp to readable format
        timestamp = json_data.get('dt')
        readable_day = datetime.fromtimestamp(timestamp, timezone.utc).strftime('%A')
        readable_date = datetime.fromtimestamp(timestamp, timezone.utc).strftime('%d/%m/%Y')
        readable_day_date = datetime.fromtimestamp(timestamp, timezone.utc).strftime('%A, %d/%m/%Y')

        # Prepare the weather data for rendering
        weather_data = {
            "name": json_data.get('name', "Unknown"),
            "day": readable_day,
            "date": readable_date,
            "day_date": readable_day_date,
            "lat": json_data['coord']['lat'],
            "lon": json_data['coord']['lon'],
            "temp_c": json_data['main']['temp'],  # Celsius from the API
            "temp_f": (json_data['main']['temp'] * 9/5) + 32,  # Convert Celsius to Fahrenheit
            "feelslike_c": json_data['main']['feels_like'],
            "temp_min": json_data['main']['temp_min'],
            "temp_max": json_data['main']['temp_max'],
            "pressure_mb": json_data['main']['pressure'],
            "humidity": json_data['main']['humidity'],
            "visibility_km": json_data['visibility'] / 1000,  # Convert meters to kilometers
            "wind_speed_kph": json_data['wind']['speed'] * 3.6,  # Convert m/s to kph
            "wind_dir": json_data['wind']['deg'],
            "gust_kph": json_data['wind'].get('gust', 0) * 3.6,  # Convert m/s to kph
            "condition_text": json_data['weather'][0]['description'],
            "condition_icon": f"http://openweathermap.org/img/wn/{json_data['weather'][0]['icon']}@2x.png",
            "rain_1h_mm": json_data.get('rain', {}).get('1h', 0),  # Rain in the last 1 hour (mm)
            "cloud_coverage": json_data['clouds']['all'],  # Cloud coverage percentage
            "country": json_data['sys']['country'],
            "timezone_offset": json_data['timezone'],
            "sunrise": datetime.fromtimestamp(json_data['sys']['sunrise'], timezone.utc).strftime('%H:%M:%S'),
            "sunset": datetime.fromtimestamp(json_data['sys']['sunset'], timezone.utc).strftime('%H:%M:%S'),
            "current_time": datetime.now().strftime('%H:%M'),  # Add current time
            "time": datetime.now().strftime('%H:%M')
        }

        return render_template('day.html', weather=weather_data, cityName=location)

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching weather data: {e}")
        return render_template('day.html', weather=None, error="Failed to connect to the weather service.")

@app.route('/night', methods=['GET', 'POST'])
def night():
    # Get the current time in the server's timezone
    current_time = datetime.now().time()
    start_time = time(19, 00)  
    end_time = time(23, 59)  

    # Check if the current time is within the allowed range
    if not (start_time <= current_time <= end_time):
        return render_template('night.html', weather=None, error="Please click the 'Day' button for day weather information.")
   
    location = session.get('location', None)

    # If the method is POST, update the location from the form
    if request.method == 'POST':
        location = request.form.get('cityName')
        if location:
            session['location'] = location  
        else:
             session.pop('location', None)  # Remove location if empty

    # Handle the case where location is None
    if not location:
        return render_template('night.html', weather=None, error="Please provide a valid location.")
    
    querystring = {
        "q": location,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        # Fetch current weather data
        response = requests.get(API_URL, params=querystring)
        response.raise_for_status()
        json_data = response.json()

        # Check if response has valid data
        if json_data.get('cod') != 200:
            return render_template('night.html', weather=None, error="Invalid city name or API error.")

        # Convert API date timestamp to readable format
        timestamp = json_data.get('dt')
        readable_day = datetime.fromtimestamp(timestamp, timezone.utc).strftime('%A')
        readable_date = datetime.fromtimestamp(timestamp, timezone.utc).strftime('%d/%m/%Y')
        readable_day_date = datetime.fromtimestamp(timestamp, timezone.utc).strftime('%A, %d/%m/%Y')

        # Prepare the weather data for rendering
        weather_data = {
            "name": json_data.get('name', "Unknown"),
            "day": readable_day,
            "date": readable_date,
            "day_date": readable_day_date,
            "lat": json_data['coord']['lat'],
            "lon": json_data['coord']['lon'],
            "temp_c": json_data['main']['temp'],  # Celsius from the API
            "temp_f": (json_data['main']['temp'] * 9/5) + 32,  # Convert Celsius to Fahrenheit
            "feelslike_c": json_data['main']['feels_like'],
            "temp_min": json_data['main']['temp_min'],
            "temp_max": json_data['main']['temp_max'],
            "pressure_mb": json_data['main']['pressure'],
            "humidity": json_data['main']['humidity'],
            "visibility_km": json_data['visibility'] / 1000,  # Convert meters to kilometers
            "wind_speed_kph": json_data['wind']['speed'] * 3.6,  # Convert m/s to kph
            "wind_dir": json_data['wind']['deg'],
            "gust_kph": json_data['wind'].get('gust', 0) * 3.6,  # Convert m/s to kph
            "condition_text": json_data['weather'][0]['description'],
            "condition_icon": f"http://openweathermap.org/img/wn/{json_data['weather'][0]['icon']}@2x.png",
            "rain_1h_mm": json_data.get('rain', {}).get('1h', 0),  # Rain in the last 1 hour (mm)
            "cloud_coverage": json_data['clouds']['all'],  # Cloud coverage percentage
            "country": json_data['sys']['country'],
            "timezone_offset": json_data['timezone'],
            "sunrise": datetime.fromtimestamp(json_data['sys']['sunrise'], timezone.utc).strftime('%H:%M:%S'),
            "sunset": datetime.fromtimestamp(json_data['sys']['sunset'], timezone.utc).strftime('%H:%M:%S'),
            "current_time": datetime.now().strftime('%H:%M'),  # Add current time
            "time": datetime.now().strftime('%H:%M')
        }

        return render_template('night.html', weather=weather_data, cityName=location)

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching weather data: {e}")
        return render_template('night.html', weather=None, error="Failed to connect to the weather service.")

def classify_precipitation(precipitation_mm):
        """Classify precipitation intensity based on mm/hour."""
        if precipitation_mm < 2.5:
            return "Light Rain"
        elif 2.5 <= precipitation_mm <= 10:
            return "Moderate Rain"
        elif 10 < precipitation_mm <= 50:
            return "Heavy Rain"
        elif 50 < precipitation_mm <= 100:
            return "Very Heavy Rain"
        else:
            return "Extreme Rain"
        
@app.route('/hourly', methods=['GET', 'POST'])
def hourly():
    location = session.get('location', None)

    # Handle POST request to update location
    if request.method == 'POST':
        location = request.form.get('cityName')
        if location:
            session['location'] = location
        else:
            session.pop('location', None)

    # Validate location input
    if not location:
        return render_template('hourly.html', weather=None, error="Please provide a valid location.")

    querystring = {
        "q": location,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        # Fetch current weather data
        response = requests.get(API_URL, params=querystring)
        response.raise_for_status()
        json_data = response.json()

        # Check if response has valid data
        if json_data.get('cod') != 200:
            return render_template('hourly.html', weather=None, error="Invalid city name or API error.")

        # Extract relevant weather features for the model
        current_weather = {
            'temp': json_data['main']['temp'],  # Temperature in Celsius
            'windspeed': json_data['wind']['speed'],  # Wind speed (m/s)
            'winddir': json_data['wind'].get('deg', 0),  # Wind direction (degrees)
            'cloudcover': json_data['clouds']['all'],  # Cloud coverage percentage
            'solarradiation': 0,  # Set to 0 or use an external source for solar radiation
            'severerisk': calculate_severe_risk(json_data),  # Calculate or fetch severe risk (can be a custom function)
        }

        hourly_forecast = []
        icon_mapping = {
            0: "0.png",  # Clear Day
            1: "1.png",  # Clear Night
            2: "2.png",  # Cloudy
            3: "3.png",  # Fog
            4: "4.png",  # Partly Cloudy Day
            5: "5.png",  # Partly Cloudy Night
        }

        if 'hourly' in json_data:
            for forecast in json_data['hourly']:
                # Example of prediction model (adjust to match your features)
                features = [
                    forecast['temp'],  # Temperature in Celsius
                    forecast['wind_speed'],  # Wind speed (m/s)
                    forecast['wind_deg'],  # Wind direction (degrees)
                    forecast['clouds'],  # Cloud coverage percentage
                    forecast.get('solarradiation', 0),  # Placeholder for solar radiation (could be from another source)
                    0,  # Placeholder for severe risk (could be calculated based on other data)
                ]
                # Assuming weather_model is a pre-trained model that outputs an icon code
                prediction = weather_model.predict([features])[0]
                hourly_forecast.append({
                    'time': forecast['dt'],
                    'temp': forecast['temp'],
                    'icon': icon_mapping.get(prediction, '0.png')
                })

        # Prepare weather data for rendering
        weather_data = {
            "name": json_data['name'],
            "temp_c": json_data['main']['temp'],
            "feelslike_c": json_data['main']['feels_like'],
            "humidity": json_data['main']['humidity'],
            "wind_speed_kph": json_data['wind']['speed'] * 3.6,  # Convert m/s to kph
            "cloud_coverage": json_data['clouds']['all'],
            "condition_icon": f"http://openweathermap.org/img/wn/{json_data['weather'][0]['icon']}@2x.png",
            "condition_text": json_data['weather'][0]['description'],
            "predicted_icon": f"static/icons/{icon_mapping.get(prediction, '0.png')}"  # Path to the predicted icon
        }

        # Print the forecast data to the console for debugging
        print("Hourly forecast data:", hourly_forecast)

        # Render the template with weather data and predicted icon
        return render_template('hourly.html', weather=weather_data, hourly_forecast=hourly_forecast)

    except requests.exceptions.RequestException as err:
        # Handle request errors gracefully
        return render_template('hourly.html', weather=None, error="Could not fetch weather data. Please try again later.")

def calculate_severe_risk(weather_data):
    # Custom function to calculate or approximate 'severerisk' based on available weather data
    # This could be based on temperature, wind speed, cloud cover, and other factors
    # For now, we will return a dummy value (you can update this based on your criteria)
    
    temp = weather_data['main']['temp']
    wind_speed = weather_data['wind']['speed']
    
    if temp > 30 and wind_speed > 10:
        return 2  # High risk
    elif temp > 20:
        return 1  # Moderate risk
    else:
        return 0  # Low risk
    
if __name__ == '__main__':
    app.run(debug=True)
# @app.route('/monthly')
# def monthly():
#     return render_template('monthly.html', weather=None) 

# @app.route('/activities')
# def monthly():
#     return render_template('activities.html', weather=None) 

