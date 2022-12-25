import machine


class Thermometer:
    def __init__(self):
        self.sensor_temp = machine.ADC(4)
        self.a = - 3.3 / (65535 * 0.001721)
        self.b = 27 + 0.706/0.001721

    def get(self):
        temp = self.a * self.sensor_temp.read_u16() + self.b
        # print(str(temp)+' '+chr(176)+'C')
        return round(temp, 1)

    def getA(self):
        read = self.sensor_temp.read_u16() * (3.3/65535)
        temp = 27 - (read - 0.706)/0.001721
        # print(str(temp)+' '+chr(176)+'C')
        return round(temp, 1)


if __name__ == '__main__':
    senser = Thermometer()
    print(senser.get())
    print(senser.getA())
