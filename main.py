import csv
import datetime
import inspect
import os.path
import re
from enum import Enum, IntEnum
from typing import List, Dict, Callable, Iterable
from itertools import groupby

from prettytable import PrettyTable

import report


class Salary:
    __currency_to_rub = {
        "AZN": 35.68,
        "BYR": 23.91,
        "EUR": 59.90,
        "GEL": 21.74,
        "KGS": 0.76,
        "KZT": 0.13,
        "RUR": 1,
        "UAH": 1.64,
        "USD": 60.66,
        "UZS": 0.0055,
    }

    def __init__(self, salary_from: List[str], salary_to: List[str], salary_currency: List[str],
                 salary_gross: List[str]):
        self.salary_from = salary_from[0]
        self.salary_to = salary_to[0]
        self.salary_currency = salary_currency[0]
        self.salary_gross = salary_gross[0] if salary_gross is not None else None

    def get_middle_salary_rub(self):
        percent = self.__currency_to_rub[self.salary_currency]
        salary_from = int(float(self.salary_from))
        salary_to = int(float(self.salary_to))
        return (salary_from + salary_to) * percent // 2


class Vacancy:
    def __init__(self, name: List[str], area_name: List[str], published_at: List[str], salary_from: List[str],
                 salary_to: List[str],
                 salary_currency: List[str], premium: List[str] = None, experience_id: List[str] = None,
                 description: List[str] = None,
                 key_skills: List[str] = None,
                 employer_name: List[str] = None, salary_gross: List[str] = None, **not_needed):
        self.name = name[0]
        self.salary = Salary(salary_from, salary_to, salary_currency, salary_gross)
        self.area_name = area_name[0]
        self.published_at = published_at[0]
        self.year = published_at[0].split('-')[0]
        self.premium = premium[0] if premium is not None else None
        self.experience_id = experience_id[0] if experience_id is not None else None
        self.description = description[0] if description is not None else None
        self.key_skills = key_skills if key_skills is not None else None
        self.employer_name = employer_name[0] if employer_name is not None else None


class VacancyForTable:
    def __init__(self, name: str, description: str, salary: str, key_skills: List[str], employer_name: str,
                 area_name: str,
                 premium: str, work_experience: List[str], date: str, **not_needed):
        self.name = name
        self.description = description
        self.key_skills = key_skills
        self.work_experience = work_experience
        self.premium = premium
        self.employer_name = employer_name
        self.salary = salary
        self.area_name = area_name
        self.date = date


class Formatter:
    @staticmethod
    def format_row(row: Vacancy) -> VacancyForTable:
        premium = 'Да' if row.premium.lower() == 'true' else 'Нет'
        salary = Formatter.format_salary(row.salary.salary_from, row.salary.salary_to, row.salary.salary_currency,
                                         row.salary.salary_gross)
        work_experience = Translators.WorkExperience[row.experience_id].value
        date = Formatter.parse_date(row.published_at)

        return VacancyForTable(
            name=row.name,
            description=row.description,
            key_skills=row.key_skills,
            work_experience=work_experience,
            premium=premium,
            employer_name=row.employer_name,
            salary=salary,
            area_name=row.area_name,
            date=date
        )
        # {
        #     'Название': row['name'],
        #     'Описание': row['description'],
        #     'Навыки': row['key_skills'],
        #     'Опыт работы': [work_experience],
        #     'Премиум-вакансия': [premium],
        #     'Компания': row['employer_name'],
        #     'Оклад': [salary],
        #     'Название региона': row['area_name'],
        #     'Дата публикации вакансии': [date],
        # }

    @staticmethod
    def format_salary(salary_from: str, salary_to: str, currency: str, gross: str) -> str:
        gross_str = 'Без вычета налогов' if gross.lower() == 'true' else 'С вычетом налогов'
        s_from = Formatter.__format_salary_amount(salary_from)
        s_to = Formatter.__format_salary_amount(salary_to)
        return f'{s_from} - {s_to} ({Translators.Currency[currency].value}) ({gross_str})'

    @staticmethod
    def __format_salary_amount(salary: int or float or str) -> str:
        return "{:,}".format(int(float(salary))).replace(',', ' ')

    @staticmethod
    def parse_date(date: str) -> str:
        year, month, day = date \
            .split('T')[0] \
            .split('-')
        return f'{day}.{month}.{year}'


class Translators:
    class WorkExperience(Enum):
        noExperience = "Нет опыта"
        between1And3 = "От 1 года до 3 лет"
        between3And6 = "От 3 до 6 лет"
        moreThan6 = "Более 6 лет"

    class WorkExperienceSorted(IntEnum):
        noExperience = 0
        between1And3 = 1
        between3And6 = 2
        moreThan6 = 3

    currency_to_rub = {
        "AZN": 35.68,
        "BYR": 23.91,
        "EUR": 59.90,
        "GEL": 21.74,
        "KGS": 0.76,
        "KZT": 0.13,
        "RUR": 1,
        "UAH": 1.64,
        "USD": 60.66,
        "UZS": 0.0055,
    }

    class Currency(Enum):
        AZN = "Манаты"
        BYR = "Белорусские рубли"
        EUR = "Евро"
        GEL = "Грузинский лари"
        KGS = "Киргизский сом"
        KZT = "Тенге"
        RUR = "Рубли"
        UAH = "Гривны"
        USD = "Доллары"
        UZS = "Узбекский сум"


class Utils:
    @staticmethod
    def p_salary(row: Vacancy) -> int:
        percent = Translators.currency_to_rub[row.salary.salary_currency]
        salary_from = int(float(row.salary.salary_from))
        salary_to = int(float(row.salary.salary_to))
        return (salary_from + salary_to) * percent // 2

    @staticmethod
    def filter(filter_name: str) -> Callable:
        filters = {
            'Навыки': lambda name, row: all(x in row.key_skills for x in name),
            'Оклад': lambda salary, row: int(float(row.salary.salary_from)) <= int(salary) <= int(
                float(row.salary.salary_to)),
            'Дата публикации вакансии': lambda date, row: datetime.datetime.strptime(row.published_at,
                                                                                     '%Y-%m-%dT%H:%M:%S%z').strftime(
                '%d.%m.%Y') == date,
            'Опыт работы': lambda name, row: row.experience_id == Translators.WorkExperience(name).name,
            'Премиум-вакансия': lambda name, row: row.premium == ('True' if name == 'Да' else 'False'),
            'Идентификатор валюты оклада': lambda name, row: row.salary.salary_currency == Translators.Currency(
                name).name,
            'Название': lambda name, row: row.name == name,
            'Название региона': lambda name, row: row.area_name == name,
            'Компания': lambda name, row: row.employer_name == name,
            'Описание': lambda name, row: row.description == name
        }
        return filters[filter_name]

    @staticmethod
    def can_aggregate(key: str) -> bool:
        return key in ['Навыки', 'Оклад', 'Дата публикации вакансии', 'Опыт работы', 'Премиум-вакансия',
                       'Идентификатор валюты оклада', 'Название', 'Название региона', 'Компания', 'Описание']

    @staticmethod
    def sort(sort_name: str) -> Callable:
        sorts = {
            'Навыки': lambda row: len(row.key_skills),
            'Оклад': Utils.p_salary,
            'Дата публикации вакансии': lambda row: datetime.datetime.strptime(row.published_at,
                                                                               '%Y-%m-%dT%H:%M:%S%z').timestamp(),
            'Опыт работы': lambda row: Translators.WorkExperienceSorted[row.experience_id],
            'Премиум-вакансия': lambda row: row.premium,
            'Идентификатор валюты оклада': lambda row: row.salary.salary_currency,
            'Название': lambda row: row.name,
            'Название региона': lambda row: row.area_name,
            'Компания': lambda row: row.employer_name,
            'Описание': lambda row: row.description
        }
        return sorts[sort_name]


class InputConnect:
    @staticmethod
    def get_vacs(grouped: Iterable, by_year: bool = True, need_div: bool = True, default: Dict = None):
        by_count = {}
        by_salary = {}
        if default is not None:
            for k, v in default.items():
                by_count[k] = v
                by_salary[k] = v
        for group, val in grouped:
            by = int(group) if by_year else group
            count = 0
            for v in val:
                count += 1
                if by not in by_count:
                    by_count[by] = 1
                else:
                    by_count[by] += 1
                if by not in by_salary:
                    by_salary[by] = v.salary.get_middle_salary_rub()
                else:
                    by_salary[by] += v.salary.get_middle_salary_rub()
            if need_div and count != 0:
                by_salary[by] = int(by_salary[by] // count)

        return by_count, by_salary

    @staticmethod
    def clear_by_city(salary_by_city, vacancies_by_city, all_count):
        for city in salary_by_city:
            salary = salary_by_city[city]
            salary_by_city[city] = int(salary // vacancies_by_city[city])

        too_small_cities = []
        for city in vacancies_by_city:
            count = vacancies_by_city[city]
            new_value = count / all_count
            if new_value < 0.01:
                too_small_cities.append(city)
            else:
                vacancies_by_city[city] = new_value

        for city in too_small_cities:
            del vacancies_by_city[city]
            del salary_by_city[city]

    @staticmethod
    def print_table(read_csv: Callable) -> Callable:
        def table(self) -> None:
            csv_generator = read_csv(self)
            header = next(csv_generator)

            (filter_name, filter_value,
             sort_query, sort_reverse,
             start, end, fields,
             err_msg) = self._DataSet__get_inputs()

            field_maps = [next(csv_generator)]
            if len(header) == 0:
                print("Пустой файл")
                return
            elif len(field_maps) == 0:
                print('Нет данных')
                return
            elif err_msg:
                print(err_msg)
                return
            field_maps += [f for f in csv_generator]
            self._DataSet__prepare_for_table(field_maps, filter_name, filter_value, sort_query, sort_reverse)
            if len(self._DataSet__table.rows) == 0:
                print("Ничего не найдено")
                return
            if end is None:
                print(self._DataSet__table.get_string(start=start, fields=fields))
            else:
                print(self._DataSet__table.get_string(start=start, end=end, fields=fields))

        def file(self) -> None:
            csv_generator = read_csv(self)
            next(csv_generator)
            prof_name = input('Введите название профессии: ')
            wkhtml_path = input('Введите путь до wkghml.exe или пустую строку для стандартного пути: ')
            wkhtml_path = os.path.abspath(
                r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe' if wkhtml_path == "" else wkhtml_path)
            vacancies = [v for v in csv_generator]
            vacancies_with_prof = list(filter(lambda v: prof_name in v.name, vacancies))
            vacs_by_year = groupby(vacancies, lambda v: v.year)
            profs_by_year = groupby(vacancies_with_prof, lambda v: v.year)
            vacs_by_city = groupby(vacancies, lambda v: v.area_name)

            vacancies_by_year, salary_by_year = InputConnect.get_vacs(vacs_by_year)
            professions_by_year, profs_salary_by_year = InputConnect.get_vacs(profs_by_year,
                                                                              default={int(k): 0 for k in
                                                                                       vacancies_by_year})

            vacancies_by_city, salary_by_city = InputConnect.get_vacs(vacs_by_city, False, False)
            InputConnect.clear_by_city(salary_by_city, vacancies_by_city, len(vacancies))

            vacancies_by_city_to_print = {k: float('{:.4f}'.format(v)) for k, v in sorted(vacancies_by_city.items(),
                                                                                          key=lambda item: item[1],
                                                                                          reverse=True)[:10]}
            salary_by_city_to_print = {k: v for k, v in
                                       sorted(salary_by_city.items(), key=lambda item: item[1], reverse=True)[:10]}

            print('Динамика уровня зарплат по годам:', salary_by_year)
            print('Динамика количества вакансий по годам:', vacancies_by_year)
            print('Динамика уровня зарплат по годам для выбранной профессии:', profs_salary_by_year)
            print('Динамика количества вакансий по годам для выбранной профессии:', professions_by_year)
            print('Уровень зарплат по городам (в порядке убывания):',
                  salary_by_city_to_print)
            print('Доля вакансий по городам (в порядке убывания):',
                  vacancies_by_city_to_print)

            rep = report.Report(salary_by_city_to_print, vacancies_by_city_to_print, salary_by_year, vacancies_by_year,
                                profs_salary_by_year, professions_by_year, prof_name)
            rep.generate_excel()
            rep.generate_image()
            rep.generate_pdf(wkhtml_path)

        return file if input('Вакансии или Статистика: ') == 'Статистика' else table


class DataSet:
    def __init__(self):
        self.file_name = None
        self.vacancies_objects: List[Vacancy] = []
        self.__RE_ALL_HTML = re.compile(r'<.*?>')
        self.__RE_ALL_NEWLINE = re.compile(r'\n|\r\n')
        self.__header: List[str] = []
        self.__header_for_table = ['№', 'Название', 'Описание', 'Навыки',
                                   'Опыт работы', 'Премиум-вакансия', 'Компания',
                                   'Оклад', 'Название региона', 'Дата публикации вакансии']
        self.__table = PrettyTable(self.__header_for_table,
                                   max_width=20, align='l', hrules=1)

    @InputConnect.print_table
    def read_csv(self) -> Vacancy or []:
        self.file_name = input('Введите название файла: ')
        with open(self.file_name, encoding="utf-8") as file:
            header = []
            file_reader = csv.reader(file)
            columns_count = 0
            for row in file_reader:
                header = row
                header[0] = 'name'
                self.__header = header
                columns_count = len(row)
                break
            yield header
            for row in file_reader:
                if "" in row or len(row) < columns_count:
                    continue
                cleared = self.__clear_field(row)
                vacancy = Vacancy(**cleared)
                self.vacancies_objects.append(vacancy)
                yield vacancy
            if len(self.vacancies_objects) == 0:
                yield
            else:
                return []

    def __prepare_for_table(self, fields: List[Vacancy], filter_name: str, filter_value: str,
                            sort_query: str, sort_reverse: bool) -> str:
        index = 0
        if filter_name != '':
            fields = list(filter(lambda x: Utils.filter(filter_name)(filter_value, x), fields))
        if sort_query != '':
            fields = sorted(fields, key=Utils.sort(sort_query), reverse=sort_reverse)
        fields = map(Formatter.format_row, fields)
        for field in fields:
            index += 1
            self.__table.add_row(
                [str(index)] + [self.__trim_row(self.__transform_skill(k, v)) for k, v in field.__dict__.items()])
        return ""

    @staticmethod
    def __transform_skill(k: str, v: List[str]) -> str:
        return '\n'.join(v) if k == 'key_skills' else v

    @staticmethod
    def __trim_row(row: str) -> str:
        return row if len(row) <= 100 else row[:100] + '...'

    def __get_inputs(self) -> (str, str, str, bool, int, int or None, List[str], str):
        filter_query = input('Введите параметр фильтрации: ')
        sort_query = input('Введите параметр сортировки: ')
        sort_reverse_query = input('Обратный порядок сортировки (Да / Нет): ')
        sort_reverse = False if sort_reverse_query in ['Нет', ''] else True
        filter_name, filter_value, err_msg = self.__parse_query(filter_query)

        if not Utils.can_aggregate(sort_query) and sort_query != '':
            err_msg = 'Параметр сортировки некорректен'
        if sort_reverse_query not in ['Нет', 'Да', '']:
            err_msg = 'Порядок сортировки задан некорректно'

        start, end = self.__prepend_rows(input('Введите диапазон вывода: '))
        fields = self.__prepend_fields(input('Введите требуемые столбцы: ').split(', '))

        return filter_name, filter_value, sort_query, sort_reverse, start, end, fields, err_msg

    def __prepend_fields(self, fields: List[str]) -> List[str]:
        if fields[0] == '' or any(filter(lambda field: field not in self.__header_for_table, fields)):
            fields = self.__header_for_table
        else:
            fields.append('№')
        return fields

    def __prepend_rows(self, rows: str) -> (int, int or None):
        rows = rows.split(' ')
        start = 0
        end = None
        if len(rows) == 2:
            start = int(rows[0]) - 1
            end = int(rows[1]) - 1
        elif len(rows) == 1 and rows[0] != '':
            start = int(rows[0]) - 1

        return start, end

    def __parse_query(self, query: str) -> (str, str, str):
        if query == "":
            return '', '', ''
        if ': ' not in query:
            return '', '', "Формат ввода некорректен"
        f_name, f_value = query.split(": ")
        if not Utils.can_aggregate(f_name):
            return '', '', "Параметр поиска некорректен"
        if f_name == "Навыки":
            f_value = f_value.split(", ")
        return f_name, f_value, ""

    def __clear_field(self, items: List[str]) -> Dict[str, List[str]]:
        field = {}
        for column, row in zip(self.__header, items):
            field[column] = list(map(self.__delete_html, self.__split_by_newline(row)))
        return field

    def __delete_html(self, item: str) -> str:
        return " ".join(re.
                        sub(self.__RE_ALL_HTML, "", item)
                        .split())

    def __split_by_newline(self, item: str) -> List[str]:
        return re.split(self.__RE_ALL_NEWLINE, item)


reader = DataSet()
reader.read_csv()
