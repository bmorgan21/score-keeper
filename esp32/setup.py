from machine import Pin, SPI
import gc9a01


def init_screen(rotation=0):
    print('Init Screen...')
    spi = SPI(2, baudrate=100000000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))

    tft = gc9a01.GC9A01(
        spi,
        240,
        240,
        dc=Pin(8, Pin.OUT),
        cs=Pin(9, Pin.OUT),
        reset=Pin(14, Pin.OUT),
        backlight=Pin(2, Pin.OUT),
        rotation=rotation)
    tft.init()
    print('Screen Ready.')
    
    return tft