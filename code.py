import framebuf
import math
import time
from epaper75B import EPD_7in5_B
from thermometer import Thermometer


def circle(buf: framebuf.FrameBuffer, x, y, r, c):
    buf.hline(x-r, y, r*2, c)
    for i in range(1, r):
        a = int(math.sqrt(r*r-i*i))  # Pythagoras!
        buf.hline(x-a, y+i, a*2, c)  # Lower half
        buf.hline(x-a, y-i, a*2, c)  # Upper half


def line_w(buf: framebuf.FrameBuffer, x1, y1, x2, y2, w, c):
    for i in range(-1*int(w/2), int(w/2)):
        for j in range(-1*int(w/2), int(w/2)):
            buf.line(x1+i, y1+j, x2+i, y2+j, c)


def plot_graph(epd: EPD_7in5_B, data: list[float]):
    cell_width = 80
    cell_height = 80
    row_count = 4
    column_count = 9
    margin_top = 130
    margin_left = 40

    # 横線
    for i in range(0, row_count+1):
        epd.imageblack.hline(margin_left, margin_top+cell_height*i,
                             column_count*cell_height, epd.BLACK)
    # 縦線
    for i in range(0, column_count+1):
        epd.imageblack.vline(margin_left+cell_width*i, margin_top,
                             row_count*cell_width, epd.BLACK)
    # グラフ
    last_point = (margin_left, int(round(250-data[0]*4)))
    for i in range(0, len(data)):
        point = (margin_left+12*i, int(round(250-data[i]*4)))
        circle(epd.imagered, point[0], point[1], 5, epd.RED)
        line_w(epd.imagered, last_point[0], last_point[1],
               point[0], point[1], 2, epd.RED)
        last_point = point
    # Y軸 ラベル
    for i in range(0, row_count+1):
        epd.writer_black.text(str(i*10), 8, margin_top+cell_height*i-10)
        epd.writer_black.text(str(i*10), column_count *
                              cell_height+48, margin_top+cell_height*i-10)
    # X軸 ラベル
    for i in range(0, column_count+1):
        epd.writer_black.text(str(i*10), margin_left +
                              cell_width*i-12, margin_top - 30)


if __name__ == '__main__':

    epd = EPD_7in5_B()
    epd.imageblack.fill(epd.WHITE)
    epd.imagered.fill(epd.WHITE)
    t = time.localtime()
    epd.writer_black.text(str('{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}'.format(
        t[0], t[1], t[2], t[3], t[4], t[5])), 5, 10, 40, True)
    thermometer = Thermometer()
    temp = thermometer.get()
    epd.writer_black.text(str(temp)+chr(176)+'C', 600, 10, 40, True)
    plot_graph(epd, [21.5, 22.0, 23.5, 24.0, 27.0, 30.0,
               28.0, 25.5, 21.5, 19.0, 10.0, 4.5, -1.0, -3.0, 7.5, 12.0, 15.0, 18.0, 20.5,
               28.0, 25.5, 21.5, 19.0, 10.0, 4.5, -1.0, -3.0, 7.5, 12.0, 15.0, 18.0, 20.5,
               28.0, 25.5, 21.5, 19.0, 10.0, 4.5, -1.0, -3.0, 7.5, 12.0, 15.0, 18.0, 20.5, ])
    epd.display()
    epd.sleep()
