import os
import ssl
import time
import wifi
import socketpool
import adafruit_requests

import board
import digitalio
import adafruit_pcd8544

import altimeter
import static

# Initialize SPI bus and control pins
display = adafruit_pcd8544.PCD8544(static.spi, static.dc, static.cs, static.reset)

# Reset display
display.fill(0)
display.show()

backlight = digitalio.DigitalInOut(board.GP9)  # backlight
backlight.switch_to_output()
backlight.value = True

# Display settings
display.bias = 4
display.contrast = 55

# Try to connect to Wi-Fi
try:
    wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
except:
    internet = False
    display.text('No WiFi', 0, 0, 1)
    display.show()
    time.sleep(0.5)
    display.fill(0)
    display.show()
else:
    display.text('WiFi', 0, 0, 1)
    display.text('Connected', 0, 8, 1)
    display.show()
    time.sleep(0.5)
    display.fill(0)
    display.show()
    internet = True

url = f'https://api.openweathermap.org/data/2.5/weather?lat={static.lat}&lon={static.lon}&appid={os.getenv("API_KEY")}'

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

P0 = 101325  # fallback station pressure in case GET fails the first time
received = False  # assume API connection was unsuccessful by default

# Cumulative ascent/descent counter
cum_asc = 0.
cum_dsc = 0.
i = 0  # seconds counter

while True:

    # Try to get the current station pressure
    # if it's the first altitude reading, or it's time to update the station pressure and WiFi is available
    if ((i == 0) | (i >= static.interval_P0)) & (internet != False):
        received = False  # "station pressure received" indicator

        display.fill(0)
        display.show()
        display.text('Updating', 0, 0, 1)
        display.text('station', 0, 8, 1)
        display.text('pressure', 0, 16, 1)
        display.show()

        try:
            response = requests.get(url)
        except:
            print('Unable to connect to API')
        else:
            if response.status_code == 200:
                data = response.json()
                P0 = data['main']['pressure'] * 100
                received = True  # set "rcvd" to true if successful
            else:
                print('API error')
        i = 0  # Reset the counter
        display.fill(0)
        display.show()

    # Set up static text
    display.text('m', 35, 0, 1)
    display.text('ft', 35, 8, 1)
    display.text('Asc', 0, 24, 1)
    display.text('Dsc', 0, 32, 1)
    display.text('m', 55, 24, 1)
    display.text('m', 55, 32, 1)

    # Display indicator if the last attempt to update the station pressure was successful
    if received:
        display.text('Rx', display.width - 11, 40, 1)

    display.show()

    # Get sensor pressure
    P = altimeter.get_sensor_pressure()

    # Calculate altitude from pressure
    h_now = altimeter.barometric_formula(P, P0)

    # Assume the first altitude reading is valid
    if i == 0:
        h_valid = h_now

    if h_now - h_valid > static.h_threshold:  # ignore differences smaller than the threshold
        cum_asc = cum_asc + (h_now - h_valid)
        h_valid = h_now

    elif h_now - h_valid < -static.h_threshold:
        cum_dsc = cum_dsc + abs(h_now - h_valid)
        h_valid = h_now

    # Display altitude
    display.text(str(h_now)[:5], 0, 0, 1)  # metres
    display.text(str(altimeter.metres_to_feet(h_now))[:5], 0, 8, 1)  # feet

    # Display cumulative ascent/descent
    display.text(str(cum_asc)[:4], 25, 24, 1)
    display.text(str(cum_dsc)[:4], 25, 32, 1)

    display.show()

    time.sleep(static.interval_P)

    # Refresh altitude text
    for x in range(0, 30):
        display.line(x, 0, x, 16, 0)
    display.show()

    # Refresh cumulative text
    for x in range(25, 45):
        display.line(x, 24, x, 38, 0)
    display.show()

    # Update the time elapsed since the last station pressure update
    i = i + static.interval_P
