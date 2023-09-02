from machine import Pin
from time import sleep

from machine import RTC

print(RTC().datetime())

pin = Pin("LED", Pin.OUT)

# while True:
#     pin.toggle()
#     sleep(1)

# Issue #117 where neeed to sleep on startup otherwis emight not boot
from time import sleep
sleep(0.5)

# import enviro firmware, this will trigger provisioning if needed
import enviro
import os

print("The RTC timestamp is reading: ")
print(RTC().datetime())


from phew import logging
# log the exception, blink the warning led, and go back to sleep
def exception(exc):
  import sys, io
  buf = io.StringIO()
  sys.print_exception(exc, buf)
  logging.exception("! " + buf.getvalue())
  warn_led(WARN_LED_BLINK)
  sleep()

# import os
# from dotenv import load_dotenv
# from python-dotenv import get_key, find_dotenv 

# influxdb_org = get_key(find_dotenv(), 'influxdb_org')
# influxdb_url = get_key(find_dotenv(), 'influxdb_url')

import secret as sc

influxdb_org = sc.influxdb_org
influxdb_url = sc.influxdb_url


try:
  # initialise enviro
  # enviro.startup()
  logging.debug("Test")
  # handle any unexpected exception that has occurred
except Exception as exc:
  enviro.exception(exc)
