# common pins
HOLD_VSYS_EN_PIN = 2
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5


# from machine import Pin
# hold_vsys_en_pin = Pin(HOLD_VSYS_EN_PIN, Pin.OUT, value=True)

from pimoroni_i2c import PimoroniI2C

i2c = PimoroniI2C(I2C_SDA_PIN, I2C_SCL_PIN, 100000)


def is_bme280():
    from breakout_bmp280 import BreakoutBMP280
    try:
        BreakoutBMP280(i2c, address=0x77)
        return True
    except:
        return False

def is_bme68x():
    from breakout_bme68x import BreakoutBME68X
    try:
        BreakoutBME68X(i2c, address=0x77)
        return True
    except:
        return False

is_bme68x()

# Assuming 'i2c' is already initialized
sensor_type = detect_sensor(i2c)
print("Detected sensor:", sensor_type)


# ===================================================================================

# from enviro.constants import *
# common pins
# HOLD_VSYS_EN_PIN              = 2
# EXTERNAL_INTERRUPT_PIN        = 3
# I2C_SDA_PIN                   = 4
# I2C_SCL_PIN                   = 5
# ACTIVITY_LED_PIN              = 6
# BUTTON_PIN                    = 7
# RTC_ALARM_PIN                 = 8
# RAIN_PIN                      = 10


# from machine import Pin
# hold_vsys_en_pin = Pin(HOLD_VSYS_EN_PIN, Pin.OUT, value=True)

# detect board model based on devices on the i2c bus and pin state
# ===========================================================================
# from pimoroni_i2c import PimoroniI2C
# i2c = PimoroniI2C(I2C_SDA_PIN, I2C_SCL_PIN, 100000)

# sensor_reset_pin = Pin(9, Pin.OUT, value=True)
# sensor_enable_pin = Pin(10, Pin.OUT, value=False)
# boost_enable_pin = Pin(11, Pin.OUT, value=False)

# i2c_devices = i2c.scan()

# For troubleshooting which devices are on the i2c bus. Can be removed.
# for device in i2c_devices:
#   print("Decimal address: ",device," | Hexa address: ",hex(device))


# import time
# from breakout_bme280 import BreakoutBME280
# from breakout_bme68x import BreakoutBME68X

# from enviro import i2c


# try:
#   bme280 = BreakoutBMP280(i2c, 0x77)
# except Exception as exc:
#   print(exc)
# try:
#   bme688 = BreakoutBME68X(i2c, address=0x77)
# except Exception as exc:
#   print(exc)

# def get_280_sensor_readings():
#   # bme280 returns the register contents immediately and then starts a new reading
#   # we want the current reading so do a dummy read to discard register contents first
#   bme280.read()
#   time.sleep(0.1)
#   bme280_data = bme280.read()


#   from ucollections import OrderedDict
#   return OrderedDict({
#     "temperature": round(bme280_data[0], 2),
#     "humidity": round(bme280_data[2], 2),
#     "pressure": round(bme280_data[1] / 100.0, 2)
#   })


# def get_688_sensor_readings():
#   bme688.read()
#   time.sleep(0.1)
#   bme688_data = bme688.read()

#   from ucollections import OrderedDict
#   return OrderedDict({
#     "temperature": round(bme688_data[0], 2),
#     "humidity": round(bme688_data[2], 2),
#     "pressure": round(bme688_data[1] / 100.0, 2)
#   })


# def main():
#   print("Start by initializing the sensors")

#   print("Getting the 280 readings:")
#   try:
#     reading280 = get_280_sensor_readings()
#     print(reading280)
#   except Exception as exc:
#     print("Exception",exc)

#   print("Now getting the 688 readings:")
#   try:
#     reading688 = get_688_sensor_readings()
#     print(reading688)
#   except Exception as exc:
#     print("Exception",exc)

# main()
