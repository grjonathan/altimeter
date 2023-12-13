import time
import math

import adafruit_pcd8544

import altimeter
import static

# Initialize SPI bus and control pins
display = adafruit_pcd8544.PCD8544(static.spi, static.dc, static.cs, static.reset)


def bar(x, y, scale):  # draws a vertical bar downwards from x,y
    x = x
    y = int(47 - y * 47 * scale)  # scale = percentage of the screen to use
    display.line(x, y, x, 47, 1)


# Display settings
display.bias = 4
display.contrast = 55

display.fill(0)
display.show()

# Define variables
coords = []
h = None
asc = 0
dsc = 0
t0 = time.monotonic()  # reference time for stopwatch
t1 = time.monotonic()  # reference time for initial bar
t2 = time.monotonic()  # reference time for initial pressure sample
t3 = time.monotonic()  # reference time for alternating ascent/descent

P0 = 101325  # standard atmospheric pressure

dt_P = 2.  # how often to sample the pressure, seconds
dt_bar = 3600 / 83  # how often to add a bar to the graph, seconds (dt_bar * 83 = time-width of graph)
dt_lcd = 1 / 8  # how often to refresh the display, seconds
h_thres = 1.5  # minimum height change to register as ascent or descent, m

while True:
    display.fill(0)
    P = altimeter.get_sensor_pressure()

    if time.monotonic() - t2 >= dt_P:
        P = altimeter.get_sensor_pressure()
        h_raw = altimeter.barometric_formula(P, P0)

        # Add cumulative ascent/descent
        if h is None:  # if an 'h' hasn't been validated yet
            h = h_raw  # assume the first 'h' is valid
        elif h_raw - h > h_thres:  # if change greater than threshold
            asc = asc + (h_raw - h)  # add descent
            h = h_raw
        elif h_raw - h < -h_thres:  # if change less than negative threshold
            dsc = dsc + abs(h_raw - h)  # add descent
            h = h_raw
        t2 = time.monotonic()  # reset time since pressure sample

    # Add bar to list
    if time.monotonic() - t1 >= dt_bar:
        P = altimeter.get_sensor_pressure()
        h_raw = altimeter.barometric_formula(P, P0)
        coords.append(h_raw)
        coords = coords[-83:]  # store only the 83 most recent readings
        hmin, hmax = min([i for i in coords]), max([i for i in coords])
        t1 = time.monotonic()  # reset time since bar was updated

    # Display bar
    if len(coords) > 1:
        for i, val in enumerate(coords):
            x = i
            y = (val - hmin) / (hmax - hmin)
            bar(x, y, 0.40)

    # Display stats
    # Cumulative ascent / descent
    if time.monotonic() - t3 > 10.:  # show ascent for 5 seconds, descent for 5 seconds
        t3 = time.monotonic()
    if time.monotonic() - t3 < 5.:
        display.text('Asc', 1, 9, 1)
        display.text(str(asc)[:5], 25, 9, 1)
        display.text('m', 65, 9, 1)
    else:
        for y in range(8, 17):  # show descent on a black background
            display.line(0, y, 83, y, 1)
        display.text('Dsc', 1, 9, 0)
        display.text(str(dsc)[:5], 25, 9, 0)
        display.text('m', 65, 9, 0)

    # Gauge pressure
    display.text('P', 1, 0, 1)
    display.text(str(int(P))[:6], 25, 0, 1)
    display.text('Pa', 65, 0, 1)

    # Time elapsed
    display.text('T', 1, 18, 1)
    elapsed_s = time.monotonic() - t0
    hr = '{:0>2}'.format(str(int(elapsed_s // 3600)))
    m = '{:0>2}'.format(str(int(elapsed_s % 3600 // 60)))
    s = '{:0>2}'.format(str(math.floor(elapsed_s % 3600 % 60)))
    display.text(f'{hr}:{m}:{s}', 25, 18, 1)

    display.show()
    time.sleep(dt_lcd)
