import framebuf
import math
import utime
from epaper75B import EPD_7in5_B
from thermometer import Thermometer
from collections import deque


def circle(buf: framebuf.FrameBuffer, point, r, c):
    x, y = point
    buf.hline(x-r, y, r*2, c)
    for i in range(1, r):
        a = int(math.sqrt(r*r-i*i))  # Pythagoras!
        buf.hline(x-a, y+i, a*2, c)  # Lower half
        buf.hline(x-a, y-i, a*2, c)  # Upper half


def line_w(buf: framebuf.FrameBuffer, point1, point2, w, c):
    x1, y1 = point1
    x2, y2 = point2
    for i in range(-1*int(w/2), int(w/2)):
        for j in range(-1*int(w/2), int(w/2)):
            buf.line(x1+i, y1+j, x2+i, y2+j, c)


class TempGraph:
    cell_width = 80
    cell_height = 80
    row_count = 4
    column_count = 9
    width = column_count*cell_width
    height = row_count*cell_height
    margin_top = 130
    margin_left = 40
    hours_per_cell = 2
    column_now = -2
    temp_max = 30
    temp_per_cell = 5
    data_count_per_hour = 4
    data_count_per_cell = hours_per_cell * data_count_per_hour
    width_per_data = cell_width/data_count_per_cell
    now_pos = column_count + column_now
    temp_zero_y = int(margin_top+cell_height * (temp_max/temp_per_cell))
    height_per_temp = cell_height/temp_per_cell

    def __init__(self, epd: EPD_7in5_B):
        self.epd = epd

    def draw_frame(self):
        # 横線
        for i in range(0, self.row_count+1):
            self.epd.imageblack.hline(
                self.margin_left, self.margin_top+self.cell_height*i, self.width, epd.BLACK)
        # 縦線
        for i in range(0, self.column_count+1):
            self.epd.imageblack.vline(
                self.margin_left+self.cell_width*i, self.margin_top, self.height, epd.BLACK)
        # Y軸 ラベル
        for i in range(0, self.row_count+1):
            temp = self.temp_max - i*self.temp_per_cell
            self.epd.writer_black.text(
                str(temp), 8, self.margin_top+self.cell_height*i-10)
            self.epd.writer_black.text(str(temp), self.width+48,
                                       self.margin_top+self.cell_height*i-10)
        # X軸 ラベル
        t = utime.localtime()
        hour = t[3]
        for i in range(0, self.column_count+1):
            value = hour-(self.now_pos-i)*self.hours_per_cell
            if value < 0:
                value += 24
            elif value > 24:
                value -= 24
            if value != hour:
                self.epd.writer_black.text(str(value), self.margin_left +
                                           self.cell_width*i-12, self.margin_top - 30)
            else:
                self.epd.writer_red.text('{:02d}:{:02d}'.format(
                    t[3], t[4]), self.margin_left +
                    self.cell_width*i-36, self.margin_top - 30)

    def plot(self, data):
        print(len(data))
        self.draw_frame()
        last_point = (0, 0)
        last_point_yesterday = (0, 0)
        for i in range(0, self.column_count*self.data_count_per_cell+1):
            x = int(self.margin_left+i*self.width_per_data)
            # current
            index = self.now_pos*self.data_count_per_cell - i
            if len(data) > index and i <= self.now_pos*self.data_count_per_cell:
                temp = data[(len(data)-1)-index]
                point = (x, self.get_temp_y(temp))
                circle(epd.imagered, point, 5, epd.RED)
                if(last_point[0] != 0):
                    line_w(epd.imagered, last_point, point, 2, epd.RED)
                last_point = point
            # yesterday
            index = index + 24*self.data_count_per_hour
            if len(data) > index:
                temp = data[(len(data)-1)-index]
                point = (x, self.get_temp_y(temp))
                circle(epd.imageblack, point, 5, epd.BLACK)
                if(last_point_yesterday[0] != 0):
                    line_w(epd.imageblack, last_point_yesterday,
                           point, 2, epd.BLACK)
                last_point_yesterday = point

    def get_temp_y(self, temp):
        return int(self.temp_zero_y-(self.height_per_temp*temp))


if __name__ == '__main__':
    data = []
    epd = EPD_7in5_B()
    thermometer = Thermometer()
    graph = TempGraph(epd)

    while True:
        epd.init()
        temp = thermometer.get()
        data.append(temp)
        if(len(data) > 300):
            data = data[100:]
        epd.imageblack.fill(epd.WHITE)
        epd.imagered.fill(epd.WHITE)
        t = utime.localtime()
        epd.writer_black.text('{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}'.format(
            t[0], t[1], t[2], t[3], t[4], t[5]), 10, 10, 40, True)
        epd.writer_black.text(str(temp)+chr(176)+'C', 640, 10, 40, True)
        graph.plot(data)
        epd.display()
        epd.sleep()
        utime.sleep(15*60)
