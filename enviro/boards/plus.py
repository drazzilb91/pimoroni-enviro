# Forking from indoor board as it is the closest to the plus board
import time  # temp
import math
from machine import Pin, ADC, UART
from picographics import PicoGraphics, DISPLAY_ENVIRO_PLUS
from pimoroni import RGBLED, Button
from pimoroni_i2c import PimoroniI2C
from pms5003 import PMS5003
from enviro import i2c
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
led.set_rgb(0, 0, 0)

# set up the buttons
button_a = Button(12, invert=True)
button_b = Button(13, invert=True)
button_x = Button(14, invert=True)
button_y = Button(15, invert=True)

# ========Initialize Pico Graphics========
display = PicoGraphics(display=DISPLAY_ENVIRO_PLUS)
display.set_backlight(1.0)

WIDTH, HEIGHT = display.get_bounds()
display.set_font("bitmap8")

# some constants we'll use for drawing
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
RED = display.create_pen(255, 0, 0)
GREEN = display.create_pen(0, 255, 0)

# setup background
BG = display.create_pen(0, 0, 0)
TEXT = display.create_pen(255, 255, 255)
PROX = display.create_pen(255, 0, 0)
LUX = display.create_pen(255, 255, 0)
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

print("Found LTR559. Part ID: 0x", "{:02x}".format(ltr559.part_id()), sep="")
time.sleep(0.25)
reading = ltr559.get_reading()
if reading is not None:
    print(
        "Light sensor current readings are, Lux:",
        reading[BreakoutLTR559.LUX],
        "Prox:",
        reading[BreakoutLTR559.PROXIMITY],
    )

# NOTE: Removing the color sensor as it is not present on the plus board
# =====================End Lights=====================

# set up analog channel for microphone
mic = ADC(Pin(26))

# configure the PMS5003 for Enviro+
pms5003 = PMS5003(
    uart=UART(1, tx=Pin(8), rx=Pin(9), baudrate=9600),
    pin_enable=Pin(3),
    pin_reset=Pin(2),
    mode="active",
)


def get_sensor_readings(seconds_since_last):
    data = bme688.read()

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


# This is the primary event loop for the program
while True:
    # read BME688
    temperature, pressure, humidity, gas, status, _, _ = bme688.read()
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

    if heater == "Stable" and ltr_reading is not None:
        led.set_rgb(0, 0, 0)
        current_time = time.ticks_ms()
        if (current_time - last_update) / 1000 >= UPDATE_INTERVAL:
            # then do an MQTT
            try:
                # mqtt_client.connect()
                # mqtt_client.publish(topic="EnviroTemperature", msg=str(corrected_temperature))
                # mqtt_client.publish(topic="EnviroHumidity", msg=str(corrected_humidity))
                # mqtt_client.publish(topic="EnviroPressure", msg=str(pressure / 100))
                # mqtt_client.publish(topic="EnviroGas", msg=str(gas))
                # mqtt_client.publish(topic="EnviroLux", msg=str(lux))
                # mqtt_client.publish(topic="EnviroMic", msg=str(mic_reading))
                # mqtt_client.publish(topic="EnviroParticulates1_0", msg=str(particulate_reading.pm_ug_per_m3(1.0)))
                # mqtt_client.publish(topic="EnviroParticulates2_5", msg=str(particulate_reading.pm_ug_per_m3(2.5)))
                # mqtt_client.publish(topic="EnviroParticulates10", msg=str(particulate_reading.pm_ug_per_m3(10)))
                # mqtt_client.disconnect()
                update_success = True
                last_update = time.ticks_ms()
                led.set_rgb(0, 50, 0)
            except Exception as e:
                print(e)
                update_success = False
                led.set_rgb(255, 0, 0)
    else:
        # light up the LED red if there's a problem with MQTT or sensor readings
        led.set_rgb(255, 0, 0)

    # turn off the backlight with A and turn it back on with B
    # things run a bit hotter when screen is on, so we're applying a different temperature offset
    if button_a.is_pressed:
        display.set_backlight(1.0)
        TEMPERATURE_OFFSET = 5
        time.sleep(0.5)
    elif button_b.is_pressed:
        display.set_backlight(0)
        TEMPERATURE_OFFSET = 3
        time.sleep(0.5)

    # Abort if button X and Y are pressed
    if button_x.is_pressed and button_y.is_pressed:
        print("Exiting")
        break

    # draw some stuff on the screen
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    display.text("Posting Enviro+ sensor data", 10, 10, WIDTH, scale=3)
    if update_success is True:
        current_time = time.ticks_ms()
        display.set_pen(GREEN)
        display.text(
            f"Last MQTTed {(current_time - last_update) / 1000:.0f} seconds ago",
            10,
            130,
            WIDTH,
            scale=3,
        )
    else:
        display.set_pen(RED)
        display.text(e, 10, 130, WIDTH, scale=3)
    display.update()

    time.sleep(1.0)
