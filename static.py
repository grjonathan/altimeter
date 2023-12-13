import board
import busio
import digitalio

# HARDWARE
# Bosch BMP280
scl_bmp280 = board.GP11
sda_bmp280 = board.GP10
# Phillips PCD8544
spi = busio.SPI(board.GP6, MOSI=board.GP7)  # serial clock, data output from main (TX)  "CLK" & "DIN"
dc = digitalio.DigitalInOut(board.GP4)  # data/command, data output from sub (RX)  "DC"
cs = digitalio.DigitalInOut(board.GP5)  # chip select  "CE"
reset = digitalio.DigitalInOut(board.GP0)  # reset  "RST"
