import board
import busio
import digitalio

# NUMERICS
interval_P = 5  # sensor pressure sample rate, seconds
interval_P0 = 600  # station pressure refresh rate, seconds
h_threshold = 2.  # minimum elevation change to register as cumulative ascent or descent, metres

# LOCATION
lat, lon = 43.7, -79.6  # coordinates for weather API call

# HARDWARE
scl_bmp280 = board.GP11
sda_bmp280 = board.GP10
spi = busio.SPI(board.GP6, MOSI=board.GP7)
dc = digitalio.DigitalInOut(board.GP4) # data/command
cs = digitalio.DigitalInOut(board.GP5) # chip select
reset = digitalio.DigitalInOut(board.GP8) # reset
