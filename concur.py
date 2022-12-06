import concurrent.futures
import concurrent.futures as cf
import os
from functools import partial
from typing import Dict

from main import DataSet
from reportv2 import Report
from cProfile import Profile
from pstats import Stats
prof = Profile()


def do_work(file_name, prof_name):
    reader = DataSet(_to_show='Статистика')
    salary_by_city_to_print, vacancies_by_city_to_print, salary_by_year, vacancies_by_year, \
    profs_salary_by_year, professions_by_year, prof_name = reader.read_csv(file_name=file_name,
                                                                           prof_name=prof_name)
    rep = Report(salary_by_year, vacancies_by_year, profs_salary_by_year, professions_by_year, prof_name)
    header, rows = rep.generate_years_table()
    return {'header': header, 'rows': rows[0], 'salary': salary_by_year, 'vacs': vacancies_by_year,
            'profs_salary': profs_salary_by_year, 'profs_vacs': professions_by_year}


def merge_dicts(origin: Dict, dicts, by: str):
    for dict in dicts:
        origin.update(dict[by].items())


if __name__ == '__main__':
    with cf.ProcessPoolExecutor() as executor:
        files = []
        prof.disable()
        csvs_dir = input('Путь до папки с csv: ')
        prof_name = input('Профессия: ')
        wkhtml_path = input('Введите путь до wkghml.exe или пустую строку для стандартного пути: ')
        prof.enable()
        wkhtml_path = os.path.abspath(
            r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe' if wkhtml_path == "" else wkhtml_path)
        for file in os.listdir(os.path.join('.', csvs_dir)):
            files.append(os.path.join('.', 'csvs', file))

        reader = partial(do_work, prof_name=prof_name)
        futures = [executor.submit(reader, file_name) for file_name in files]
        output = []

        for future in concurrent.futures.as_completed(futures, timeout=None):
            output.append(future.result())
        header = output[0]['header']
        rows = sorted(map(lambda data: data['rows'], output), key=lambda row: row[0])
        salary_by_year = {}
        merge_dicts(salary_by_year, output, 'salary')
        vacs_by_year = {}
        prof_salary_by_year = {}
        prof_vacs_by_year = {}
        merge_dicts(vacs_by_year, output, 'vacs')
        merge_dicts(prof_vacs_by_year, output, 'profs_vacs')
        merge_dicts(prof_salary_by_year, output, 'profs_salary')
        output = []
        rows.sort(key=lambda row: row[0])
        rep = Report({}, {}, {}, {}, prof_name)
        rep.generate_excel(header, rows)
        rep.generate_image(count_by_year=dict(sorted(vacs_by_year.items(), key=lambda s: s[0])),
                           prof_count_by_year=dict(sorted(prof_vacs_by_year.items(), key=lambda s: s[0])),
                           salary_by_year=dict(sorted(salary_by_year.items(), key=lambda s: s[0])),
                           prof_salary_by_year=dict(sorted(prof_salary_by_year.items(), key=lambda s: s[0])))

        rep.generate_pdf(wkhtml_path=wkhtml_path, years_table_header=header, years_table=rows)

        prof.disable()
        prof.dump_stats('concur.stats')
        with open('concur_output.txt', 'wt') as _output:
            stats = Stats('concur.stats', stream=_output)
            stats.sort_stats('cumulative', 'time')
            stats.print_stats()
