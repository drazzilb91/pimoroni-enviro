# Forking from indoor board as it is the closest to the plus board
import time # temp
import math
from picographics import PicoGraphics, DISPLAY_ENVIRO_PLUS
from pimoroni import RGBLED
from pimoroni_i2c import PimoroniI2C
from enviro import i2c

from breakout_bme68x import BreakoutBME68X
bme688 = BreakoutBME68X(i2c, address=0x77)
print("Got BME688 Sensor")

#======================Initialize Pico Graphics======================
display = PicoGraphics(display=DISPLAY_ENVIRO_PLUS)
display.set_backlight(1.0)

led = RGBLED(6, 7, 10, invert=True)  # setting pins for the RGB led
led.set_rgb(0, 0, 0)

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
#======================End of initialize Pico Graphics======================

#======================Lights======================
# NOTE: Removing the color sensor as it is not present on the plus board and adding the light sensor
# from breakout_bh1745 import BreakoutBH1745
from breakout_ltr559 import BreakoutLTR559
PINS_BREAKOUT_GARDEN = {"sda": 4, "scl": 5}
PINS_PICO_EXPLORER = {"sda": 20, "scl": 21}
i2c2 = PimoroniI2C(**PINS_BREAKOUT_GARDEN)
ltr559 = BreakoutLTR559(i2c2)

print("Found LTR559. Part ID: 0x", '{:02x}'.format(ltr559.part_id()), sep="")
time.sleep(0.25)
reading = ltr559.get_reading()
if reading is not None:
  print("Light sensor current readings are, Lux:", reading[BreakoutLTR559.LUX], "Prox:", reading[BreakoutLTR559.PROXIMITY])

# NOTE: Removing the color sensor as it is not present on the plus board
#======================End Lights======================

def lux_from_rgbc(r, g, b, c):
  if g < 1:
      tmp = 0
  elif (c / g < 0.160):
      tmp = 0.202 * r + 0.766 * g
  else:
      tmp = 0.159 * r + 0.646 * g
  tmp = 0 if tmp < 0 else tmp
  integration_time = 160
  gain = 1
  return round(tmp / gain / integration_time * 160)

def colour_temperature_from_rgbc(r, g, b, c):
  if (g < 1) or (r + g + b < 1):
      return 0
  r_ratio = r / (r + g + b)
  b_ratio = b / (r + g + b)
  e = 2.71828
  ct = 0
  if c / g < 0.160:
      b_eff = min(b_ratio * 3.13, 1)
      ct = ((1 - b_eff) * 12746 * (e ** (-2.911 * r_ratio))) + (b_eff * 1637 * (e ** (4.865 * b_ratio)))
  else:
      b_eff = min(b_ratio * 10.67, 1)
      ct = ((1 - b_eff) * 16234 * (e ** (-2.781 * r_ratio))) + (b_eff * 1882 * (e ** (4.448 * b_ratio)))
  if ct > 10000:
      ct = 10000
  return round(ct)

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

  bh1745.measurement_time_ms(160)
  r, g, b, c = bh1745.rgbc_raw()

  from ucollections import OrderedDict
  return OrderedDict({
    "temperature": temperature,
    "humidity": humidity,
    "pressure": pressure,
    "gas_resistance": gas_resistance,
    "aqi": aqi,
    "luminance": lux_from_rgbc(r, g, b, c),
    "color_temperature": colour_temperature_from_rgbc(r, g, b, c)
  })
