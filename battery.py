# This example shows how to read the voltage from a LiPo battery connected to a Raspberry Pi Pico via our Pico Lipo SHIM
# and uses this reading to calculate how much charge is left in the battery.
# It then displays the info on the screen of Pico Display.
# Remember to save this code as main.py on your Pico if you want it to run automatically!

from machine import ADC, Pin


class Battery:
    vsys = ADC(29)  # reads the system input voltage
    # reading GP24 tells us whether or not USB power is connected
    charging = Pin(24, Pin.IN)
    conversion_factor = 3 * 3.3 / 65535
    # these are our reference voltages for a full/empty battery, in volts
    full_battery = 4.2
    # the values could vary by battery size/manufacturer so you might need to adjust them
    empty_battery = 2.8
    battery_range = full_battery - empty_battery

    def getSOC(self):
        # convert the raw ADC read into a voltage, and then a percentage
        voltage = self.getVoltage()
        percentage = ((voltage - self.empty_battery) / self.battery_range)*100
        if percentage > 100:
            percentage = 100.00
        # print('{:.0f} % {:.2f} V'.format(percentage, voltage))
        return percentage

    def getVoltage(self):
        return self.vsys.read_u16() * self.conversion_factor

    def isCharge(self):
        return self.charging.value() == 1


if __name__ == '__main__':
    senser = Battery()
    print(senser.getSOC())
    print(senser.getVoltage())
