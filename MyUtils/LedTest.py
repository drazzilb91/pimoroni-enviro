from machine import Pin
from time import sleep

from machine import RTC

print(RTC().datetime())

pin = Pin("LED", Pin.OUT)

while True:
    pin.toggle()
    sleep(1)