import framebuf
import math
from epaper75B import EPD_7in5_B
from dataCollector import DataCollector
import utime


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


class GraphData:
    def __init__(self, data: DataCollector, cell_height, offset):
        self.data = data
        self.unit = (self.data.max - self.data.min) / 2
        self.max = math.ceil(self.data.max + self.unit)
        if(self.unit == 0):
            self.height_per_unit = 0
            self.zero_y = 0
        else:
            self.height_per_unit = cell_height/self.unit
            self.zero_y = int(offset+cell_height * (self.max/self.unit))
        self.last_pos = (0, 0)

    def get_pos(self, x, value):
        self.last_pos = (x, int(self.zero_y-(self.height_per_unit*value)))
        return self.last_pos

    def round(self, value):
        return round(value, 3-self.data.scale)


class GraphPaper:
    cell_width = 80
    cell_height = 80
    row_count = 4
    column_count = 9
    width = column_count*cell_width
    height = row_count*cell_height
    margin_top = 130
    margin_left = 40
    hours_per_cell = 2
    column_now = -1
    now_pos = column_count + column_now

    def __init__(self, data1: DataCollector, data2: DataCollector, data_interval: int):
        self.data_count_per_hour = int((60*60)/data_interval)
        self.data_count_per_cell = self.hours_per_cell * self.data_count_per_hour
        self.width_per_data = self.cell_width/self.data_count_per_cell
        self.epd = EPD_7in5_B()
        self.data1 = data1
        self.data2 = data2

    def display(self):
        self.epd.init()
        self.series1 = GraphData(
            self.data1, self.cell_height, self.margin_top)
        self.series2 = GraphData(
            self.data2, self.cell_height, self.margin_top)
        self.epd.imageblack.fill(self.epd.WHITE)
        self.epd.imagered.fill(self.epd.WHITE)
        t = utime.localtime()
        self.epd.writer_black.text('{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}'.format(
            t[0], t[1], t[2], t[3], t[4], t[5]), 10, 10, 40, True)
        self.epd.writer_black.text(
            str(self.series1.round(self.data2.last_value))+'V', 500, 10, 40, True)
        self.epd.writer_black.text(
            str(self.series2.round(self.data1.last_value))+chr(176)+'C', 630, 10, 40, True)
        self.plot()
        self.epd.display()
        self.epd.sleep()

    def plot(self):
        self.draw_frame()
        for i in range(0, self.column_count*self.data_count_per_cell+1):
            if i > self.now_pos*self.data_count_per_cell:
                continue
            x = int(self.margin_left+i*self.width_per_data)
            index = self.now_pos*self.data_count_per_cell - i
            self.plot_series(self.series1, index, x, 1)
            self.plot_series(self.series2, index, x, 2)

    def plot_series(self, series: GraphData, index, x, color):
        if(color == 1):
            display = self.epd.imagered
            color = self.epd.RED
        else:
            display = self.epd.imageblack
            color = self.epd.BLACK

        data = series.data.get_data()
        if len(data) <= index:
            return
        value = data[(len(data)-1)-index]
        last_pos = series.last_pos
        point = series.get_pos(x, value)
        circle(display, point, 5, color)
        if(last_pos[0] != 0):
            line_w(display, last_pos, point, 2, color)

    def draw_frame(self):
        # 横線
        for i in range(0, self.row_count+1):
            self.epd.imageblack.hline(
                self.margin_left, self.margin_top+self.cell_height*i, self.width, self.epd.BLACK)
        # 縦線
        for i in range(0, self.column_count+1):
            self.epd.imageblack.vline(
                self.margin_left+self.cell_width*i, self.margin_top, self.height, self.epd.BLACK)
        # Y軸 ラベル
        for i in range(0, self.row_count+1):
            value1 = self.series1.max - i*self.series1.unit
            self.epd.writer_black.text(
                str(self.series1.round(value1)), 8, self.margin_top+self.cell_height*i-10)
            value2 = self.series2.max - i*self.series2.unit
            self.epd.writer_black.text(str(self.series1.round(value2)), self.width+48,
                                       self.margin_top+self.cell_height*i-10, rightFit=True)
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


if __name__ == '__main__':
    count1 = 0
    count2 = 0

    def get1():
        global count1
        count1 += 1
        return count1
    data1 = DataCollector(get1, 'A')

    def get2():
        global count2
        count2 += 1
        return count2*count2
    data2 = DataCollector(get2, 'B')

    for i in range(0, 5):
        data1.add()
        data1.commit()
        data2.add()
        data2.commit()

    graph = GraphPaper(data1, data2, 60*10)
    graph.display()
