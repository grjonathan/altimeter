import board

# NUMERICS
interval_P = 1  # sensor pressure sample rate, seconds
interval_P0 = 600  # station pressure refresh rate, seconds (should be divisible by static.interval_P)
h_threshold = 2.  # minimum elevation change to register as cumulative ascent or descent, metres

# LOCATION
lat, lon = 43.7, -79.6  # coordinates for weather API call

# HARDWARE
scl_lcd = board.GP17
sda_lcd = board.GP16
scl_bmp280 = board.GP11
sda_bmp280 = board.GP10

# DISPLAY
# Custom LCD characters
asc = bytearray([0B00000,
                 0B00100,
                 0B01110,
                 0B10101,
                 0B00100,
                 0B00100,
                 0B00100,
                 0B00000])

dsc = bytearray([0B00000,
                 0B00100,
                 0B00100,
                 0B00100,
                 0B10101,
                 0B01110,
                 0B00100,
                 0B00000])

rcvd = bytearray([0B00000,
                  0B00000,
                  0B00001,
                  0B00011,
                  0B10110,
                  0B11100,
                  0B01000,
                  0B00000])
