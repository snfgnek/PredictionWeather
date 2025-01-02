# app.py
from flask import Flask, request, render_template, jsonify
import os
import requests
from dataclasses import dataclass #yt

app = Flask(__name__)

# Use your OpenWeatherMap API key
api_key = os.getenv('API_KEY', '1e966323c33f0d2fc4f0998d97533e82')

@dataclass
class WeatherData:
    main: str
    description:str
    icon: str
    temperature : int

def get_lan_lon(city_name, state_code, country_code, API_key):
    resp = requests.get(
        f'https://api.openweathermap.org/data/2.5/weather?q={city_name},{state_code},{country_code}&appid={API_key}'
    ).json()

    # Extract latitude and longitude
    coord = resp.get('coord', {})
    lat = coord.get('lat')
    lon = coord.get('lon')
    return lat, lon

def get_current_weather(lat, lon, API_key):
    resp = requests.get(f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_key}&units=metric').json()

    # Extract specific data
    df = WeatherData(
        main = resp.get('weather')[0].get('main'),
        description = resp.get('weather')[0].get('description'),
        icon = resp.get('weather')[0].get('icon'),
        temperature = int(resp.get('main').get('temp'))
    )
    return df

    # Display data
    print("Current Weather Data:")
    print(f"Temperature: {temperature} °C")
    print(f"Condition: {weather_main}")
    print(f"Description: {weather_description}")
    print(f"Wind Speed: {wind_speed} m/s")
    print(f"Cloud Cover: {cloud_cover}%")

def main(city_name, state_name, country_name):
    lat, lon = get_lan_lon(city_name, state_name, country_name, api_key)
    weather_data = get_current_weather(lat, lon, api_key)
    return weather_data

if __name__ == "__main__":
    # Correct function call with separate arguments
    lat, lon = get_lan_lon('Kuala Lumpur', 'KL', 'Malaysia', api_key)
    print(get_current_weather(lat,lon, api_key))
