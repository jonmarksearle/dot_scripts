#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "requests",
#   "meteostat",
#   "pandas"
# ]
# ///

import requests
import sys
import json
from datetime import datetime, timedelta
from meteostat import Point, Hourly

# Test location: Cobram, Victoria (Approx)
LAT = -35.92
LON = 145.65
TZ = "Australia/Melbourne"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"TESTING: {title}")
    print(f"{'='*60}")

def test_open_meteo():
    print_header("Open-Meteo (Free, No Key)")
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "temperature_2m",
        "models": "bom_access_global",
        "timezone": TZ,
        "forecast_days": 1
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        temp = data['hourly']['temperature_2m'][12] # Midday-ish
        print(f"✅ SUCCESS: Open-Meteo (BOM Model) accessed.")
        print(f"   Sample Data (Cobram ~12pm): {temp}°C")
        print(f"   Model Used: {data.get('hourly_units', {}).get('temperature_2m')}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

def test_meteostat():
    print_header("Meteostat (Python Lib, No Key)")
    try:
        # Define location (Cobram)
        # Note: Meteostat uses nearby stations if exact coords aren't a station
        location = Point(LAT, LON)
        
        # Get yesterday's data (historical)
        start = datetime.now() - timedelta(days=1)
        end = datetime.now()
        
        data = Hourly(location, start, end)
        data = data.fetch()
        
        if not data.empty:
            print(f"✅ SUCCESS: Meteostat accessed.")
            print(f"   Records found: {len(data)}")
            print(f"   Last Temp Recorded: {data['temp'].iloc[-1]}°C")
        else:
            print("⚠️  WARNING: Meteostat returned no data (might be no nearby station in their DB for Cobram).")
    except Exception as e:
        print(f"❌ FAILED: {e}")

def test_bom_ftp():
    print_header("Official BOM FTP (The 'QBits' Way)")
    from ftplib import FTP
    
    try:
        ftp = FTP('ftp.bom.gov.au', timeout=15)
        ftp.login()
        print("✅ SUCCESS: Connected to ftp.bom.gov.au (Anonymous)")
        
        # Check for the famous IDV10753 file
        ftp.cwd('anon/gen/fwo')
        files = ftp.nlst()
        if 'IDV10753.xml' in files:
             print("   Found IDV10753.xml (Victoria Forecast)")
        else:
             print("   ⚠️ IDV10753.xml not found in listing (unexpected).")
        
        ftp.quit()
    except Exception as e:
         print(f"❌ FAILED: {e}")

def test_weatherapi():
    print_header("WeatherAPI.com (Commercial, Key Required)")
    # NOTE: I do not have a key, so I expect a 401/403
    url = "http://api.weatherapi.com/v1/current.json"
    params = {"key": "INVALID_KEY", "q": "Cobram"}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code in [401, 403]:
            print("✅ EXPECTED RESULT: 401/403 Forbidden (Key Required)")
            print(f"   Msg: {response.json().get('error', {}).get('message')}")
        else:
            print(f"❓ UNEXPECTED: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAILED to connect: {e}")

def test_open_weather_map():
    print_header("OpenWeatherMap (Commercial, Key Required)")
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": LAT, "lon": LON, "appid": "INVALID_KEY"}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 401:
            print("✅ EXPECTED RESULT: 401 Unauthorized (Key Required)")
            print(f"   Msg: {response.json().get('message')}")
        else:
            print(f"❓ UNEXPECTED: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAILED to connect: {e}")

if __name__ == "__main__":
    print("RUNNING WEATHER API CHECKS...")
    test_open_meteo()
    test_meteostat()
    test_bom_ftp()
    test_weatherapi()
    test_open_weather_map()
