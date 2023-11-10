import os
import ssl
import time
import wifi
import socketpool
import adafruit_requests

import busio
from lcd.lcd import LCD
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
from lcd.lcd import CursorMode

import altimeter
import static

# Talk to the LCD at I2C address 0x27
lcd = LCD(I2CPCF8574Interface(busio.I2C(static.scl_lcd, static.sda_lcd), 0x27), num_rows=2, num_cols=16)
lcd.clear()
lcd.set_backlight(True)

# Create custom LCD characters (only need to run once for the LCD?)
lcd.create_char(0, static.asc)
lcd.create_char(1, static.dsc)
lcd.create_char(2, static.rcvd)

# Try to connect to Wi-Fi
try:
    wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
except:
    internet = False
    lcd.clear()
    lcd.print('No WiFi')
    time.sleep(0.5)
    lcd.clear()
else:
    lcd.print('WiFi Connected')
    time.sleep(0.5)
    lcd.clear()
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

        lcd.clear()
        lcd.print('Updating station pressure')  # update display

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
                print('API returned error')
        i = 0  # Reset the counter
        lcd.clear()

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
    lcd.set_cursor_pos(0, 6)
    lcd.print('m')
    lcd.set_cursor_pos(1, 6)
    lcd.print('ft')
    lcd.set_cursor_pos(0, 0)
    lcd.print(str(h_now)[:5])  # metres
    lcd.set_cursor_pos(1, 0)
    lcd.print(str(altimeter.metres_to_feet(h_now))[:5])  # feet

    # Display cumulative ascent/descent
    lcd.set_cursor_pos(0, 9)
    lcd.write(0)  # up icon
    lcd.set_cursor_pos(1, 9)
    lcd.write(1)  # down icon
    lcd.set_cursor_pos(0, 10)
    lcd.print(str(cum_asc)[:4])
    lcd.set_cursor_pos(1, 10)
    lcd.print(str(cum_dsc)[:4])

    # Show a checkmark if the last attempt to update the station pressure was successful
    if received:
        lcd.set_cursor_pos(0, 15)
        lcd.write(2)

    time.sleep(static.interval_P)

    # Update the time elapsed since the last station pressure update
    i = i + static.interval_P
