
from utime import time, sleep
from thermometer import Thermometer
from battery import Battery
import _thread
from dataCollector import DataCollector
from graphPager import GraphPaper

interval_get_value = 20
interval_commit_value = 60*10
interval_display = 60*20

if __name__ == '__main__':
    thermometer = Thermometer()
    temp_date = DataCollector(thermometer.get)

    battery = Battery()
    soc_data = DataCollector(battery.getVoltage)

    def update_data():
        last_display_time = time()
        while True:
            now = time()
            temp_date.add()
            soc_data.add()
            if(now - last_display_time >= interval_commit_value):
                temp_date.commit()
                print('commit temp:{}, {}, {}'.format(
                    temp_date.average, temp_date.max, temp_date.min))
                soc_data.commit()
                print('commit battery:{}, {}, {}'.format(
                    soc_data.average, soc_data.max, soc_data.min))
                last_display_time = time()
            sleep(interval_get_value)

    sensor_thread = _thread.start_new_thread(update_data, ())

    graph = GraphPaper(temp_date, soc_data, interval_commit_value)
    while True:
        print('start display')
        print('temp:{}, {}'.format(temp_date.get_data(), temp_date.scale))
        print('battery:{}, {}'.format(soc_data.get_data(), soc_data.scale))
        graph.display()
        print('end display')
        sleep(interval_display)
