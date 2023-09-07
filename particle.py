'''
Particle Sensor Example

This example requires seperate MicroPython drivers for the PMS5003 particulate sensor.
(You can find it at https://github.com/pimoroni/pms5003-micropython )
or install from PyPi by searching for 'pms5003-micropython' in Thonny's 'Tools > Manage Packages'

'''
from utime import sleep
from picographics import PicoGraphics, DISPLAY_ENVIRO_PLUS
from pimoroni import RGBLED
# from lib.pms5003 import PMS5003, PMS5003CmdResponse, PMS5003Data
from lib.pms5003 import *
import machine
import time

print("""particle.py - Continuously print all data values.
and draw a pretty histogram on display
""")


# Configure the PMS5003 for Enviro+
pms5003 = PMS5003(
    uart=machine.UART(1, tx=machine.Pin(8), rx=machine.Pin(9), baudrate=9600),
    pin_enable=machine.Pin(3),
    pin_reset=machine.Pin(2),
    mode="active"
)

display = PicoGraphics(display=DISPLAY_ENVIRO_PLUS)
display.set_backlight(1.0)

# Setup RGB Led
led = RGBLED(6, 7, 10, invert=True)
led.set_rgb(0, 0, 0)

# Setup background
BG = display.create_pen(0, 0, 0)
TEXT = display.create_pen(255, 255, 255)
PM10 = display.create_pen(255, 0, 0)
PM25 = display.create_pen(255, 255, 0)
PM100 = display.create_pen(0, 255, 0)
PM125 = display.create_pen(255, 255, 0)
PM1000 = display.create_pen(255, 255, 0)
display.set_pen(BG)
display.clear()

# array for storing
results = []


# Drawing routines
def draw_background():
    display.set_pen(BG)
    display.clear()
    display.set_pen(TEXT)
    display.text("PMS5003 Sensor", 5, 10, scale=3)


def draw_txt_overlay(sensor_data):
    display.set_pen(PM10)
    display.text("PM1.0: {0}".format(sensor_data.pm_ug_per_m3(1.0)), 5, 60, scale=3)
    display.set_pen(PM25)
    display.text("PM2.5: {0}".format(sensor_data.pm_ug_per_m3(2.5)), 5, 80, scale=3)
    display.set_pen(PM100)
    display.text("PM10: {0}".format(sensor_data.pm_ug_per_m3(10)), 5, 100, scale=3)


def draw_hist(results_array):

    result_index = 0
    for result in results_array:
        display.set_pen(PM100)
        display.rectangle(2 * result_index, 240 - result.pm_ug_per_m3(10), 2, 240)
        display.set_pen(PM25)
        display.rectangle(2 * result_index, 240 - result.pm_ug_per_m3(2.5), 2, 240)
        display.set_pen(PM10)
        display.rectangle(2 * result_index, 240 - result.pm_ug_per_m3(1.0), 2, 240)
        result_index += 1


# while True:
#     draw_background()
#     print("Checking for data...")
#     print(pms5003.data_available())
#     print("Reading data...")
#     data = pms5003.read()
#     print(data)
#     results.append(data)

#     if (len(results) > 120):  # Scroll the result list by removing the first value
#         results.pop(0)



#     draw_hist(results)
#     draw_txt_overlay(data)
#     display.update()
#     time.sleep(0.5)



# # Define the PMS5003 command
# PMS5003_CMD_SLEEP = b'\xe4\x00\x00'

# # Create a UART object
# uart = machine.UART(1, tx=machine.Pin(8), rx=machine.Pin(9), baudrate=9600)


# print("setting to passive mode")
# pms5003.cmd_mode_passive()
# time.sleep(1)

# # check mode
# print("checking mode")
# print(pms5003._mode)

# time.sleep(1)

# print("Sending command to sleep")
# # Send the command to the PMS5003 sensor
# uart.write(PMS5003_CMD_SLEEP)
# print("Leaving in passive mode and sleeping for 30 seconds. Then will request data again")
# time.sleep(30)
# passivedata = pms5003.read()
# print(passivedata)

# # set active mode
# print("setting to active mode")
# pms5003.cmd_mode_active()
# print("sleeping for 5 seconds")
# time.sleep(5)



import json

def pms5003_to_json(pms5003_data):
    data_dict = {
        "pm1_0_ug_per_m3": pms5003_data.pm_ug_per_m3(1.0),
        "pm2_5_ug_per_m3": pms5003_data.pm_ug_per_m3(2.5),
        "pm10_ug_per_m3": pms5003_data.pm_ug_per_m3(10),
        "pm1_0_atm_ug_per_m3": pms5003_data.pm_ug_per_m3(1.0, atmospheric_environment=True),
        "pm2_5_atm_ug_per_m3": pms5003_data.pm_ug_per_m3(2.5, atmospheric_environment=True),
        "pm10_atm_ug_per_m3": pms5003_data.pm_ug_per_m3(None, atmospheric_environment=True),
        "particles_0_3_per_0_1l": pms5003_data.pm_per_1l_air(0.3),
        "particles_0_5_per_0_1l": pms5003_data.pm_per_1l_air(0.5),
        "particles_1_0_per_0_1l": pms5003_data.pm_per_1l_air(1.0),
        "particles_2_5_per_0_1l": pms5003_data.pm_per_1l_air(2.5),
        "particles_5_0_per_0_1l": pms5003_data.pm_per_1l_air(5.0),
        "particles_10_0_per_0_1l": pms5003_data.pm_per_1l_air(10.0),
    }
    return json.dumps(data_dict)



# check data available
print("checking data available")
print(pms5003.data_available())

# read data
holder = []
print("reading data")
holder.append(pms5003.read())
print(holder)
print("Data available? ", pms5003.data_available())

print("sleeping for 10 seconds")
time.sleep(10)

print("Data available? ", pms5003.data_available())
newdata = pms5003.read()
print(newdata)
holder.append(newdata)

# pms5003.pm_ug_per_m3(1.0)
# print("pm_ug_per_m3(1.0): ", newdata.pm_ug_per_m3(1.0))
# print("Full Holder:")
# print(holder)

json_data = pms5003_to_json(newdata)
print(json_data)
