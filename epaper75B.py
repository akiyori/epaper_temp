# *****************************************************************************
# * | File        :	  Pico_ePaper-7.5-B.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2021-05-27
# # | Info        :   python demo
# -----------------------------------------------------------------------------

from machine import Pin, SPI
import framebuf
import utime
import font.writer

# Display resolution
EPD_WIDTH = 800
EPD_HEIGHT = 480

RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13


class EPD_7in5_B:
    WHITE = 0x00
    BLACK = 0xff
    RED = 0xff

    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)

        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.buffer_balck = bytearray(self.height * self.width // 8)
        self.buffer_red = bytearray(self.height * self.width // 8)
        self.imageblack = font.writer.Display(
            self.buffer_balck, self.width, self.height, framebuf.MONO_HLSB)
        self.imagered = font.writer.Display(
            self.buffer_red, self.width, self.height, framebuf.MONO_HLSB)
        self.writer_black = font.writer.Writer(
            self.imageblack, "hgn")
        self.writer_black.wrap = False
        self.writer_red = font.writer.Writer(self.imagered, "hgn")
        self.writer_red.wrap = False
        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def module_exit(self):
        self.digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200)

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)

    def WaitUntilIdle(self):
        print("e-Paper busy")
        while(self.digital_read(self.busy_pin) == 0):   # Wait until the busy_pin goes LOW
            self.delay_ms(20)
        self.delay_ms(20)
        print("e-Paper busy release")

    def TurnOnDisplay(self):
        self.send_command(0x12)  # DISPLAY REFRESH
        self.delay_ms(100)  # !!!The delay here is necessary, 200uS at least!!!
        self.WaitUntilIdle()

    def init(self):
        # EPD hardware init start
        self.reset()

        self.send_command(0x06)     # btst
        self.send_data(0x17)
        self.send_data(0x17)
        # If an exception is displayed, try using 0x38
        self.send_data(0x28)
        self.send_data(0x17)

#         self.send_command(0x01)  # POWER SETTING
#         self.send_data(0x07)
#         self.send_data(0x07)     # VGH=20V,VGL=-20V
#         self.send_data(0x3f)     # VDH=15V
#         self.send_data(0x3f)     # VDL=-15V

        self.send_command(0x04)  # POWER ON
        self.delay_ms(100)
        self.WaitUntilIdle()

        self.send_command(0X00)   # PANNEL SETTING
        self.send_data(0x0F)      # KW-3f   KWR-2F	BWROTP 0f	BWOTP 1f

        self.send_command(0x61)     # tres
        self.send_data(0x03)     # source 800
        self.send_data(0x20)
        self.send_data(0x01)     # gate 480
        self.send_data(0xE0)

        self.send_command(0X15)
        self.send_data(0x00)

        self.send_command(0X50)     # VCOM AND DATA INTERVAL SETTING
        self.send_data(0x11)
        self.send_data(0x07)

        self.send_command(0X60)     # TCON SETTING
        self.send_data(0x22)

        self.send_command(0x65)     # Resolution setting
        self.send_data(0x00)
        self.send_data(0x00)     # 800*480
        self.send_data(0x00)
        self.send_data(0x00)

        return 0

    def Clear(self):

        high = self.height
        if(self.width % 8 == 0):
            wide = self.width // 8
        else:
            wide = self.width // 8 + 1

        self.send_command(0x10)
        for j in range(0, high):
            for i in range(0, wide):
                self.send_data(0xff)

        self.send_command(0x13)
        for j in range(0, high):
            for i in range(0, wide):
                self.send_data(0x00)

        self.TurnOnDisplay()

    def ClearRed(self):

        high = self.height
        if(self.width % 8 == 0):
            wide = self.width // 8
        else:
            wide = self.width // 8 + 1

        self.send_command(0x10)
        for j in range(0, high):
            for i in range(0, wide):
                self.send_data(0xff)

        self.send_command(0x13)
        for j in range(0, high):
            for i in range(0, wide):
                self.send_data(0xff)

        self.TurnOnDisplay()

    def ClearBlack(self):

        high = self.height
        if(self.width % 8 == 0):
            wide = self.width // 8
        else:
            wide = self.width // 8 + 1

        self.send_command(0x10)
        for j in range(0, high):
            for i in range(0, wide):
                self.send_data(0x00)

        self.send_command(0x13)
        for j in range(0, high):
            for i in range(0, wide):
                self.send_data(0x00)

        self.TurnOnDisplay()

    def display(self):
        self.imageblack.show()
        self.imagered.show()

        high = self.height
        if(self.width % 8 == 0):
            wide = self.width // 8
        else:
            wide = self.width // 8 + 1

        # send black data
        self.send_command(0x10)
        for j in range(0, high):
            for i in range(0, wide):
                self.send_data(~self.buffer_balck[i + j * wide])

        # send red data
        self.send_command(0x13)
        for j in range(0, high):
            for i in range(0, wide):
                self.send_data(self.buffer_red[i + j * wide])

        self.TurnOnDisplay()

    def sleep(self):
        self.delay_ms(2000)
        print("sleep")
        self.send_command(0x02)  # power off
        self.WaitUntilIdle()
        self.send_command(0x07)  # deep sleep
        self.send_data(0xa5)

    def display_sample(self):
        self.imageblack.fill(0xff)
        self.imagered.fill(0x00)

        self.imageblack.text("Waveshare", 5, 10, 0x00)
        self.imagered.text("Pico_ePaper-7.5-B", 5, 40, 0xff)
        self.imageblack.text("Raspberry Pico", 5, 70, 0x00)

        self.imageblack.vline(10, 90, 60, 0x00)
        self.imageblack.vline(120, 90, 60, 0x00)
        self.imagered.hline(10, 90, 110, 0xff)
        self.imagered.hline(10, 150, 110, 0xff)
        self.imagered.line(10, 90, 120, 150, 0xff)
        self.imagered.line(120, 90, 10, 150, 0xff)

        self.imageblack.rect(10, 180, 50, 80, 0x00)
        self.imageblack.fill_rect(70, 180, 50, 80, 0x00)
        self.imagered.rect(10, 300, 50, 80, 0xff)
        self.imagered.fill_rect(70, 300, 50, 80, 0xff)

        for k in range(0, 3):
            for j in range(0, 3):
                for i in range(0, 5):
                    self.imageblack.fill_rect(
                        200+100+j*200, i*20+k*200, 100, 10, 0x00)
                for i in range(0, 5):
                    self.imagered.fill_rect(
                        200+0+j*200, i*20+100+k*200, 100, 10, 0xff)
        self.display()
