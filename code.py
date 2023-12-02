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
    time.sleep(0.7)
    display.fill(0)
    display.show()
else:
    display.text('WiFi', 0, 0, 1)
    display.text('Connected', 0, 8, 1)
    display.show()
    time.sleep(0.7)
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

s = 0  # reset seconds counter
t0 = time.time()  # record start time

while True:
    # Try to get the current station pressure
    # if it's the first altitude reading, or it's time to update the station pressure and WiFi is available
    if ((s == 0) | (s >= static.interval_P0)) & internet:
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
            display.fill(0)
            display.show()
            display.text('API error 1', 0, 0, 1)
            display.show()
            time.sleep(0.7)
        else:
            if response.status_code == 200:
                data = response.json()
                P0 = data['main']['pressure'] * 100
                received = True  # set received indicator to true if successful
            else:
                display.fill(0)
                display.show()
                display.text('API error 2', 0, 0, 1)
                display.show()
                time.sleep(0.7)

        t0 = time.time()  # record time at last update (the last time we were in this loop)
        s = 0  # reset seconds counter

        display.fill(0)
        display.show()

    # Set up static text
    display.text('m', 35, 0, 1)
    display.text('ft', 35, 8, 1)
    display.text('Asc', 0, 23, 1)
    display.text('Dsc', 0, 31, 1)
    display.text('m', 55, 23, 1)
    display.text('m', 55, 31, 1)

    # Display indicator if the last attempt to update the station pressure was successful
    if received:
        display.text('Rx', display.width - 11, 0, 1)
        display.rect(2, display.height - 4, display.width - 4, 4, 1)
        display.show()

    # Get sensor pressure
    P = altimeter.get_sensor_pressure()

    # Calculate altitude from pressure
    h_now = altimeter.barometric_formula(P, P0)

    # Calculate cumulative ascent/descent
    # Assume the first altitude reading is valid
    if s == 0:
        h_valid = h_now

    if h_now - h_valid > static.h_threshold:  # ignore differences smaller than the threshold
        cum_asc = cum_asc + (h_now - h_valid)
        h_valid = h_now

    elif h_now - h_valid < -static.h_threshold:
        cum_dsc = cum_dsc + abs(h_now - h_valid)
        h_valid = h_now

    # Prepare altitude strings
    disp_m = str(h_now)[:5]
    disp_ft = str(altimeter.metres_to_feet(h_now))[:5]
    display.text(disp_m, 0, 0, 1)  # metres
    display.text(disp_ft, 0, 8, 1)  # feet

    # Prepare cumulative ascent/descent strings
    disp_cum_asc = str(cum_asc)[:4]
    disp_cum_dsc = str(cum_dsc)[:4]
    display.text(disp_cum_asc, 25, 23, 1)
    display.text(disp_cum_dsc, 25, 31, 1)

    # Stage progress bar for display
    if (s > 0) & received:
        prog = round(s / (static.interval_P0 - static.interval_P) * 8)
        for n in range(0, prog):
            for row in [2, 3]:
                display.line(3 + n * 10, display.height - row, 10 + n * 10, display.height - row, 1)

    display.show()
    time.sleep(static.interval_P)  # HOLD

    # Refresh altitude text (white out the exact same pixels)
    display.text(disp_m, 0, 0, 0)  # metres
    display.text(disp_ft, 0, 8, 0)  # feet
    display.text(disp_cum_asc, 25, 23, 0)
    display.text(disp_cum_dsc, 25, 31, 0)
    display.show()

    # Update the time elapsed since the last station pressure update
    s = time.time() - t0
