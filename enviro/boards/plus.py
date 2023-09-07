# Forking from indoor board as it is the closest to the plus board
import time  # temp
import math
from machine import Pin, ADC, UART
from picographics import PicoGraphics, DISPLAY_ENVIRO_PLUS
from pimoroni import RGBLED, Button
from pimoroni_i2c import PimoroniI2C
from enviro import i2c
from adcfft import ADCFFT
# comment out the next line if no particulate sensor
from pms5003 import PMS5003
from enviro.constants import *

# some other variables we'll use to keep track of stuff
current_time = 0
last_update = 0
update_success = False
e = "Wait a minute"


# set up the BME688
from breakout_bme68x import BreakoutBME68X, STATUS_HEATER_STABLE

bme688 = BreakoutBME68X(i2c, address=0x77)
print("Got BME688 Sensor")

# set up the LED
led = RGBLED(6, 7, 10, invert=True)  # setting pins for the RGB led
led.set_rgb(50, 50, 50)

# set up the buttons
button_a = Button(12, invert=True)
button_b = Button(13, invert=True)
button_x = Button(14, invert=True)
button_y = Button(15, invert=True)

#========= Define Functions =========
# def graphic_equaliser():
#     m_arr = [0 for _ in range(16)]
#     i = 0

#     adcfft.update()
#     m = 0
#     for x in range(5, 240):
#         v = adcfft.get_scaled(x, 144)
#         m = max(m, v)
#         v = min(239, v)
#         v = 239 - v
#         display.line(x - 5, v, x - 5, 239)
#     m_arr[i] = min(255, m)
#     i += 1
#     if i >= len(m_arr):
#         i = 0
#     ms = int(sum(m_arr) / len(m_arr))
#     led.set_rgb(0, ms, 0)


def adjust_to_sea_pressure(pressure_hpa, temperature, altitude):
    """
    Adjust pressure based on your altitude.

    credits to @cubapp https://gist.github.com/cubapp/23dd4e91814a995b8ff06f406679abcf
    """

    # Adjusted-to-the-sea barometric pressure
    adjusted_hpa = pressure_hpa + ((pressure_hpa * 9.80665 * altitude) / (287 * (273 + temperature + (altitude / 400))))
    return adjusted_hpa


def describe_pressure(pressure_hpa):
    """Convert pressure into barometer-type description."""
    pressure_hpa += 0.5
    if pressure_hpa < 970:
        description = "storm"
    elif 970 <= pressure_hpa < 990:
        description = "rain"
    elif 990 <= pressure_hpa < 1010:
        description = "change"
    elif 1010 <= pressure_hpa < 1030:
        description = "fair"
    elif pressure_hpa >= 1030:
        description = "dry"
    else:
        description = ""
    return description


def describe_humidity(corrected_humidity):
    """Convert relative humidity into good/bad description."""
    corrected_humidity += 0.5
    if 40 < corrected_humidity < 60:
        description = "good"
    else:
        description = "bad"
    return description


def describe_light(lux):
    """Convert light level in lux to descriptive value."""
    lux += 0.5
    if lux < 50:
        description = "dark"
    elif 50 <= lux < 100:
        description = "dim"
    elif 100 <= lux < 500:
        description = "light"
    else: # Replaced "elif lux >= 500" with "else" as it is equivalent but also covers any case not thought of and clears an error in returning a description that is possibly undefined
        description = "bright"
    return description


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


#=========== End of Define Functions =========

# ========Initialize Pico Graphics========
display = PicoGraphics(display=DISPLAY_ENVIRO_PLUS)
display.set_backlight(1.0)

# some constants we'll use for drawing
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
RED = display.create_pen(255, 0, 0)
GREEN = display.create_pen(0, 255, 0)
CYAN = display.create_pen(0, 255, 255)
MAGENTA = display.create_pen(200, 0, 200)
YELLOW = display.create_pen(200, 200, 0)
BLUE = display.create_pen(0, 0, 200)
FFT_COLOUR = display.create_pen(255, 0, 255)
GREY = display.create_pen(75, 75, 75)

WIDTH, HEIGHT = display.get_bounds()
display.set_font("bitmap8")

# setup background
BG = display.create_pen(0, 0, 0)
TEXT = display.create_pen(255, 255, 255)
MIC = display.create_pen(0, 255, 255)
PROX = display.create_pen(255, 0, 0)
LUX = display.create_pen(255, 255, 0)
PM10 = display.create_pen(255, 0, 0)
PM25 = display.create_pen(255, 255, 0)
PM100 = display.create_pen(0, 255, 0)
PM125 = display.create_pen(255, 255, 0)
PM1000 = display.create_pen(255, 255, 0)
display.set_pen(BG)
display.clear()

def draw_graph(lux_value, prox_value):
    scaled_lux = int(200 / 1600 * lux_value)
    scaled_prox = int(200 / 1600 * prox_value)
    display.set_pen(BG)
    display.clear()
    display.set_pen(LUX)
    display.rectangle(0, 240 - scaled_lux, 120, scaled_lux)
    display.text("PROX: {0}".format(prox_value), 125, 120, scale=2)
    display.set_pen(PROX)
    display.text("LUX: {0}".format(lux_value), 5, 120, scale=2)
    display.rectangle(120, 240 - scaled_prox, 120, scaled_prox)
    display.set_pen(TEXT)
    display.text("Light+Prox Sensor", 5, 10, scale=2)
    display.text("PROX: {0}".format(prox_value), 125, 120, scale=2)
    display.update()

# Draw blank graph
draw_graph(0, 0)
# ========End of initialize Pico Graphics========

# =====================Lights=====================
# NOTE: Removing the color sensor as it is not present on the plus board and adding the light sensor
# from breakout_bh1745 import BreakoutBH1745
from breakout_ltr559 import BreakoutLTR559

# TODO: Consider removing the following 3 lines
PINS_BREAKOUT_GARDEN = {"sda": 4, "scl": 5}
PINS_PICO_EXPLORER = {"sda": 20, "scl": 21}
# TODO: choose one of the i2c imports and remove the other
i2c2 = PimoroniI2C(**PINS_BREAKOUT_GARDEN)
ltr559 = BreakoutLTR559(i2c2)

# print("Found LTR559. Part ID: 0x", "{:02x}".format(ltr559.part_id()), sep="")
# time.sleep(0.25)
# reading = ltr559.get_reading()
# if reading is not None:
#     print(
#         "Light sensor current readings are, Lux:",
#         reading[BreakoutLTR559.LUX],
#         "Prox:",
#         reading[BreakoutLTR559.PROXIMITY],
#     )

# NOTE: Removing the color sensor as it is not present on the plus board
# =====================End Lights=====================

mode = "sensors"  # start off in sensor mode

# these values will get updated later on
min_temperature = 100.0
max_temperature = 0.0
min_gas = 100000.0
max_gas = 0.0


# set up analog channel for microphone
mic = ADC(Pin(26))
# array for storing microphone readings
mic_readings = []
# Settings for bandwith and side
BANDWIDTH = 2000
SAMPLE_N = 240

# setup
led.set_rgb(255, 0, 120)
display.set_backlight(BRIGHTNESS)
display.set_pen(RED)
display.text("waiting for sensors", 0, 0, WIDTH, scale=3)
display.update()


# configure the PMS5003 for Enviro+
pms5003 = PMS5003(
    uart=UART(1, tx=Pin(8), rx=Pin(9), baudrate=9600),
    pin_enable=Pin(3),
    pin_reset=Pin(2),
    mode="active",
)

# Array for storing particulate readings
pm_results = []

#========== Functions supporting the equaliser mode ==========
# Drawing routines
def draw_background():
    if mode == "equaliser":
      label_text = "Sound Sensor"
    else:
      label_text = "PMS5003 Sensor"

    display.set_pen(BG)
    display.clear()
    display.set_pen(TEXT)
    display.text(label_text, 5, 10, scale=3)


def draw_txt_overlay(sensor_data):
    if mode == "equaliser":
      display.set_pen(MIC)
      display.text("Peak: {0}".format(sensor_data), 5, 60, scale=3)
    else:
      display.set_pen(PM10)
      display.text("PM1.0: {0}".format(sensor_data.pm_ug_per_m3(1.0)), 5, 60, scale=3)
      display.set_pen(PM25)
      display.text("PM2.5: {0}".format(sensor_data.pm_ug_per_m3(2.5)), 5, 80, scale=3)
      display.set_pen(PM100)
      display.text("PM10: {0}".format(sensor_data.pm_ug_per_m3(10)), 5, 100, scale=3)


def draw_wave(results_array):

    result_index = 0
    for result in results_array:
        display.set_pen(MIC)
        display.pixel(result_index, int(120 + result))
        result_index += 1


def read_mic():
    return mic.read_u16()

def take_sample(frequency, length=240):
    buffer = []
    for index in range(length):
        buffer.append(read_mic())
        time.sleep(1 / frequency)
    return buffer

#========== End of Functions supporting the equaliser mode ==========

def get_sensor_readings(seconds_since_last):
    data = bme688.read()

    # the gas sensor gives a few weird readings to start, lets discard them
    temperature, pressure, humidity, gas, status, gas_index, meas_index = bme688.read()
    time.sleep(0.5)
    temperature, pressure, humidity, gas, status, gas_index, meas_index = bme688.read()
    time.sleep(0.5)

    temperature = round(data[0], 2)
    pressure = round(data[1] / 100.0, 2)
    humidity = round(data[2], 2)
    gas_resistance = round(data[3])
    # an approximate air quality calculation that accounts for the effect of
    # humidity on the gas sensor
    # https://forums.pimoroni.com/t/bme680-observed-gas-ohms-readings/6608/25
    aqi = round(math.log(gas_resistance) + 0.04 * humidity, 1)
    # luminance = ltr559.get_lux()
    # proximity = ltr559.get_proximity()
    luminance = reading[BreakoutLTR559.LUX]
    proximity = reading[BreakoutLTR559.PROXIMITY]

    from ucollections import OrderedDict

    return OrderedDict(
        {
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure,
            "gas_resistance": gas_resistance,
            "aqi": aqi,
            "luminance": luminance,
            "proximity": proximity,
            "gas_index": gas_index,
            "meas_index": meas_index
        }
    )


def status_handler(mode, status, ip):
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    # display.text("Network: {}".format(WIFI_CONFIG.SSID), 10, 10, scale=2)
    display.text("Network: ", 10, 10, scale=2)
    status_text = "Connecting..."
    if status is not None:
        if status:
            status_text = "Connection successful!"
        else:
            status_text = "Connection failed!"

    display.text(status_text, 10, 30, scale=2)
    display.text("IP: {}".format(ip), 10, 60, scale=2)
    display.update()

# ! This is to be removed prior to PR. It is a temporary hack to get the code to run for me while still displaying the
# ! relevant information
# import enviro
from enviro import config, logging, cache_upload, is_upload_needed, cached_upload_count, upload_readings,halt, save_reading
  # is an upload destination set?
def upload_reading_checker(reading):
    if config.destination:
        # if so cache this reading for upload later
        logging.debug(f"> caching reading for upload")
        cache_upload(reading)

    # if we have enough cached uploads...
    if is_upload_needed():
        logging.info(f"> {cached_upload_count()} cache file(s) need uploading")
        if not upload_readings():
            halt("! reading upload failed")
        else:
            logging.info(f"> {cached_upload_count()} cache file(s) not being uploaded. Waiting until there are {config.upload_frequency} file(s)")
    else:
        # otherwise save reading to local csv file (look in "/readings")
        logging.debug(f"> saving reading locally")
        save_reading(reading)



# This is the primary event loop for the program
from ucollections import OrderedDict
last_update = time.ticks_ms()

while True:
    current_time = time.ticks_ms()
    if (current_time - last_update) / 1000 >= UPDATE_INTERVAL:
        mode = "upload"

    # Abort if button X and Y are pressed
    if button_x.is_pressed and button_y.is_pressed:
        print("Exiting")
        with open("pms5003.txt", "w") as f:
            for result in pm_results:
                f.write(str(result))
                f.write("\n")
        with open("mic.txt", "w") as f:
            for result in mic_readings:
                f.write(str(result))
                f.write("\n")
                
        break
    
    # turn off the backlight with A and turn it back on with B
    # things run a bit hotter when screen is on, so we're applying a different temperature offset
    # switch between sensor and equaliser mode with X and Y
    if button_a.is_pressed:
        display.set_backlight(BRIGHTNESS)
        TEMPERATURE_OFFSET = 5
        time.sleep(0.2)
    elif button_b.is_pressed:
        display.set_backlight(0)
        TEMPERATURE_OFFSET = 3
        time.sleep(0.2)
    elif button_x.is_pressed:
        mode = "sensors"
        display.set_backlight(BRIGHTNESS)
        TEMPERATURE_OFFSET = 5
        time.sleep(0.2)
    elif button_y.is_pressed:
        mode = "equaliser"
        display.set_backlight(BRIGHTNESS)
        TEMPERATURE_OFFSET = 5
        time.sleep(0.2)

    if mode == "sensors":
      # read BME688
      temperature, pressure, humidity, gas, status, _, _ = bme688.read()
      heater = "Stable" if status & STATUS_HEATER_STABLE else "Unstable"

      # correct temperature and humidity using an offset
      corrected_temperature = temperature - TEMPERATURE_OFFSET
      dewpoint = temperature - ((100 - humidity) / 5)
      corrected_humidity = 100 - (5 * (corrected_temperature - dewpoint))

      # record min and max temperatures
      if corrected_temperature >= max_temperature:
          max_temperature = corrected_temperature
      if corrected_temperature <= min_temperature:
          min_temperature = corrected_temperature

      # record min and max gas readings
      if gas > max_gas:
          max_gas = gas
      if gas < min_gas:
          min_gas = gas

      # convert pressure into hpa
      pressure_hpa = pressure / 100

      # correct pressure
      pressure_hpa = adjust_to_sea_pressure(pressure_hpa, corrected_temperature, altitude)

      # read LTR559
      ltr_reading = ltr559.get_reading()
      lux = ltr_reading[BreakoutLTR559.LUX]
      prox = ltr_reading[BreakoutLTR559.PROXIMITY]

      # read particulate sensor and put the results into the array
      # comment out if no PM sensor
      data = pms5003.read()
      # print("PM Data: ", data)
      pm_results.append(data)
      if (len(pm_results) > 120):  # Scroll the result list by removing the first value
          pm_results.pop(0)

      if heater == "Stable" and ltr_reading is not None:
          led.set_rgb(0, 0, 0)

          # draw some stuff on the screen
          display.set_pen(BLACK)
          display.clear()

          # draw particulate graph on screen, comment out if no PM sensor
          draw_hist(pm_results)

          # draw the top box
          display.set_pen(GREY)
          display.rectangle(0, 0, WIDTH, 60)

          # pick a pen colour based on the temperature
          display.set_pen(GREEN)
          if corrected_temperature > 30:
              display.set_pen(RED)
          if corrected_temperature < 10:
              display.set_pen(CYAN)
          display.text(f"{corrected_temperature:.1f}°C", 5, 15, WIDTH, scale=4)

          # draw temp max and min
          display.set_pen(CYAN)
          display.text(f"min {min_temperature:.1f}", 125, 5, WIDTH, scale=3)
          display.set_pen(RED)
          display.text(f"max {max_temperature:.1f}", 125, 30, WIDTH, scale=3)

          # draw the first column of text
          display.set_pen(WHITE)
          display.text(f"rh {corrected_humidity:.0f}%", 0, 75, WIDTH, scale=3)
          display.text(f"{pressure_hpa:.0f}hPa", 0, 125, WIDTH, scale=3)
          display.text(f"{lux:.0f} lux", 0, 175, WIDTH, scale=3)

          # draw the second column of text
          display.text(f"{describe_humidity(corrected_humidity)}", 125, 75, WIDTH, scale=3)
          display.text(f"{describe_pressure(pressure_hpa)}", 125, 125, WIDTH, scale=3)
          display.text(f"{describe_light(lux)}", 125, 175, WIDTH, scale=3)

          # draw bar for gas
          if min_gas != max_gas:
              # light the LED and set pen to red if the gas / air quality reading is less than 50%
              if (gas - min_gas) / (max_gas - min_gas) > GAS_ALERT:
                  led.set_rgb(255, 0, 0)
                  display.set_pen(RED)
                  print("Gas Alert, min_gas: ", min_gas, " max_gas: ", max_gas, " gas: ", gas)
              else:
                  display.set_pen(GREEN)

              display.rectangle(236, HEIGHT - round((gas - min_gas) / (max_gas - min_gas) * HEIGHT), 4, round((gas - min_gas) / (max_gas - min_gas) * HEIGHT))
              display.text("gas", 185, 210, WIDTH, scale=3)

          display.update()
          time.sleep(0.5)
    elif mode == "equaliser":
      # display.set_pen(BLACK)
      # display.clear()
      # display.set_pen(FFT_COLOUR)
      # display.text("mic", 0, 0, WIDTH, scale=3)
      # graphic_equaliser()
      # display.update()

      mic_readings = take_sample(BANDWIDTH, SAMPLE_N)

      # Rescale for display
      for result_index in range(len(mic_readings)):
          mic_readings[result_index] = (mic_readings[result_index] - 33100) / 30
      # Display Upates
      draw_background()
      draw_wave(mic_readings)
      draw_txt_overlay(max(mic_readings))
      display.update()
      time.sleep(0.2)
    elif mode == "upload":
        
        # draw some stuff on the screen
        display.set_pen(BLACK)
        display.clear()
        display.set_pen(WHITE)
        display.text("Posting Enviro+ sensor data", 10, 10, WIDTH, scale=3)
        
        e = None  # define the variable 'e' before the try-except block
        heater = None
        ltr_reading = None
        sensor_data = None

        try:
            # read BME688
            temperature, pressure, humidity, gas_resistance, status, gas_index, meas_index = bme688.read()
            heater = "Stable" if status & STATUS_HEATER_STABLE else "Unstable"

            # correct temperature and humidity using an offset
            corrected_temperature = temperature - TEMPERATURE_OFFSET
            dewpoint = temperature - ((100 - humidity) / 5)
            corrected_humidity = 100 - (5 * (corrected_temperature - dewpoint))

            # read LTR559
            ltr_reading = ltr559.get_reading()
            lux = ltr_reading[BreakoutLTR559.LUX]
            prox = ltr_reading[BreakoutLTR559.PROXIMITY]

            # read mic
            mic_reading = mic.read_u16()

            # read particle sensor
            particulate_reading = pms5003.read()

            sensor_data = {
                "temperature": temperature,
                "humidity": humidity,
                "pressure": pressure,
                "gas_resistance": gas_resistance,
                "luminance": lux,
                "proximity": prox,
                "gas_index": gas_index,
                "meas_index": meas_index
                }
        except Exception as exception:
            e = exception  # assign the exception to the variable 'e'

        # use the variable 'e' in the 'else' block
        if e is not None:
            display.set_pen(RED)
            display.text(str(e), 10, 130, WIDTH, scale=3)
        else:
            display.set_pen(GREEN)
            display.text(
                f"Last Sampled {(current_time - last_update) / 1000:.0f} seconds ago",
                10,
                130,
                WIDTH,
                scale=3,
            )
            
        display.update()


        if (heater == "Stable") and (ltr_reading is not None):
            led.set_rgb(0, 0, 0)

            try:
                

                upload_reading_checker(reading=sensor_data)
                # mqtt_client.connect()
                # mqtt_client.publish(topic="EnviroTemperature", msg=str(corrected_temperature))
                # mqtt_client.disconnect()
                update_success = True
                last_update = time.ticks_ms()
                led.set_rgb(0, 50, 0)
                mode = "sensors"
                reading = None
                sensor_data = None
            except Exception as exception:
                print(exception)
                update_success = False
                led.set_rgb(255, 0, 0)
        else:
            # light up the LED red if there's a problem with MQTT or sensor readings
            led.set_rgb(255, 0, 0)

    time.sleep(1.0)

