import csv
import os.path as pth
from typing import List
from report import check_file


class Splitter:
    def __init__(self):
        file = pth.relpath(input('Путь до csv: '))
        if not pth.exists(file):
            raise FileNotFoundError('Путь неверный')
        self.file = file
        self.file_name = pth.basename(file)
        self.file_count = 0

    def split(self, folder: str) -> None:
        if not pth.exists(folder):
            raise FileNotFoundError('Папки не существует')
        dest = pth.relpath(folder)
        with open(self.file, encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = []
            curr_year = 0
            header = next(reader)
            for row in reader:
                year = row[-1][:4]
                if curr_year == 0:
                    curr_year = year
                elif year != curr_year:
                    self.save_csv(header, rows, dest, curr_year)
                    curr_year = year
                    rows = []
                rows.append(row)
            self.save_csv(header, rows, dest, curr_year)
            rows = []

    def save_csv(self, header: List[str], rows: List[List[str]], dest: str, year: int or str):
        file_dest = pth.relpath(pth.join(dest, self.file_name[:-4] + '-' + str(year) + '.csv'))
        check_file('csv', file_dest)
        with open(file_dest, 'w', newline='',
                  encoding='utf-8') as csv_file:
            wr = csv.writer(csv_file)
            wr.writerow(header)
            wr.writerows(rows)


splt = Splitter()
splt.split(input('Куда сохранить файлы: '))
