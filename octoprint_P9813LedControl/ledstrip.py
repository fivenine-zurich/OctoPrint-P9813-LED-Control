# Based on  Philip Leder's ledstrip.py (https://github.com/schlank/Catalex-Led-Strip-Driver-Raspberry-Pi)
# adapted to gpiozero

import time
from gpiozero import LED, Device


class LEDStrip:

    def __init__(self, clock, data):
        self.__clock = clock
        self.__data = data
        self.__delay = 0

        try:
            self.__clockLed = LED(self.__clock)
            self.__dataLed = LED(self.__data)
        except (ImportError, RuntimeError):
            # Revert to mock pins if not running on raspberry pi
            from gpiozero.pins.mock import MockFactory
            Device.pin_factory = MockFactory()
            self.__clockLed = LED(self.__clock)
            self.__dataLed = LED(self.__data)

    def __sendclock(self):
        self.__clockLed.off()
        time.sleep(self.__delay)
        self.__clockLed.on()
        time.sleep(self.__delay)

    def __send32zero(self):
        for x in range(32):
            self.__dataLed.off()
            self.__sendclock()

    def __senddata(self, dx):
        self.__send32zero()

        for x in range(32):
            if ((dx & 0x80000000) != 0):
                self.__dataLed.on()
            else:
                self.__dataLed.off()

            dx <<= 1
            self.__sendclock()

        self.__send32zero()

    def __getcode(self, dat):
        tmp = 0

        if ((dat & 0x80) == 0):
            tmp |= 0x02

        if ((dat & 0x40) == 0):
            tmp |= 0x01

        return tmp

    def setcolourrgb(self, red, green, blue):

        dx = 0
        dx |= 0x03 << 30
        dx |= self.__getcode(blue)
        dx |= self.__getcode(green)
        dx |= self.__getcode(red)
        dx |= blue << 16
        dx |= green << 8
        dx |= red

        self.__senddata(dx)

    def setcolourwhite(self):
        self.setcolourrgb(255, 255, 255)

    def setcolouroff(self):
        self.setcolourrgb(0, 0, 0)

    def setcolourred(self):
        self.setcolourrgb(255, 0, 0)

    def setcolourgreen(self):
        self.setcolourrgb(0, 255, 0)

    def setcolourblue(self):
        self.setcolourrgb(0, 0, 255)

    def setcolourhex(self, hex):
        try:
            hexcolour = int(hex, 16)
            red = int((hexcolour & 255 * 255 * 255) / (255 * 255))
            green = int((hexcolour & 255 * 255) / 255)
            blue = hexcolour & 255

            self.setcolourrgb(red, green, blue)

        except:
            hexcolour = 0
            print("Error converting Hex input (%s) a colour." % hex)

    def cleanup(self):
        self.setcolouroff()
        self.__clockLed.close()
        self.__dataLed.close()
