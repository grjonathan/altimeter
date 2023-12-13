import busio
import static
import adafruit_bmp280


def get_sensor_pressure(scl=static.scl_bmp280, sda=static.sda_bmp280):
    i2c = busio.I2C(scl, sda)
    sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x77)
    P = sensor.pressure * 100
    i2c.deinit()
    return P  # pascal


def barometric_formula(P, P0):
    h = 44330 * (1 - (P / P0) ** (1 / 5.255))
    return h  # metres
