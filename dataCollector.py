import math


def GetScale(x):
    log = math.log10(abs(x))
    if(log > 0):
        return math.ceil(log)
    else:
        return int(math.floor(log))


class DataCollector:
    max = -10000
    min = 10000
    count_max = 100

    def __init__(self, fn_get_value, name=''):
        self.commited_data = []
        self.data_count = 0
        self.average = 0
        self.average_whole = 0
        self.scale = 0
        self.last_value = 0
        self.fn_get_value = fn_get_value
        self.name = name

    def add(self):
        value = self.fn_get_value()
        self.average = (self.data_count * self.average +
                        value) / (self.data_count+1)
        self.data_count += 1
        self.max = max(self.max, value)
        self.min = min(self.min, value)
        self.last_value = value

    def commit(self):
        self.data_count = 0
        self.commited_data.append(self.average)
        if(len(self.commited_data) > self.count_max):
            self.commited_data = self.commited_data[1:]

        # 全期間での平均を計算
        self.average_whole = ((len(self.commited_data)-1) * self.average_whole +
                              self.average) / len(self.commited_data)
        # 平均値からスケールを計算
        self.scale = GetScale(self.average_whole)

    def get_data(self):
        return self.commited_data


if __name__ == '__main__':
    count = 0

    def get():
        global count
        count += 1
        return count
    datac = DataCollector(get)
    for i in range(0, 3):
        for i in range(0, 3):
            datac.add()
        datac.commit()
    print(datac.get_data())  # [2.0, 5.0, 8.0]
