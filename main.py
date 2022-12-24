from cProfile import Profile
from pstats import Stats

# prof = Profile()
# prof.disable()
import csv
import datetime
import os.path
import re
from enum import Enum, IntEnum
from typing import List, Dict, Callable, Iterable, Tuple
from itertools import groupby
from prettytable import PrettyTable
import report
from report import Report

to_show = 'Статистика'


# prof.enable()


class Salary:
    """Класс для представления зарплаты.

    Attributes:
        salary_from (str): Нижняя граница з\\п
        salary_to (str): Верхняя граница з\\п
        salary_currency (str): Валюта
        salary_gross (str or None): З\\п с учетом налогов или нет
    """
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
                 salary_gross: List[str] = None):
        """Инициализирует объект Salary. Принимает значения в виде массивов из одного элемента, и берет этот элемент.

        Args:
            salary_from (List[str]): Нижняя граница з\\п
            salary_to (List[str]): Верхняя граница з\\п
            salary_currency (List[str]): Валюта
            salary_gross (List[str] or None): з\\п с учетом налогов или нет

            >>> type(Salary(['10'], ['20'], ['RUR'], None)).__name__
            'Salary'
            >>> Salary(['10'], ['20'], ['RUR'], None).salary_from
            '10'
            >>> Salary(['10'], ['20'], ['RUR'], None).salary_to
            '20'
            >>> Salary(['10'], ['20'], ['RUR'], None).salary_currency
            'RUR'
        """
        self.salary_from = salary_from[0]
        self.salary_to = salary_to[0]
        self.salary_currency = salary_currency[0]
        self.salary_gross = salary_gross[0] if salary_gross is not None else None

    def get_middle_salary_rub(self) -> int:
        """Вычисляет средную зарплату на вакансии и переводит в рубли с округлением.

            Returns:
                int: Средняя зарплата в рублях.

        """
        percent = self.__currency_to_rub[self.salary_currency]
        salary_to = int(float(self.salary_to))
        return (int(float(self.salary_from)) + salary_to) * percent // 2

    def format_salary(self) -> str:
        """Приводит финансовую информацию к строке вида {от} - {до} ({валюта}) ({налог})

            Returns:
                str: Строка с полной финансовой информацией
        """
        gross_str = 'Без вычета налогов' if self.salary_gross.lower() == 'true' else 'С вычетом налогов'
        s_from = self.__format_salary_amount(self.salary_from)
        s_to = self.__format_salary_amount(self.salary_to)
        return f'{s_from} - {s_to} ({Translators.Currency[self.salary_currency].value}) ({gross_str})'

    def __format_salary_amount(self, salary: int or float or str) -> str:
        """Приводит з\\п к виду xxx xxx xxx

            Returns:
                str: з\\п с округленная з\\п с пробелами через каждые три знака
        """
        return "{:,}".format(int(float(salary))).replace(',', ' ')


class VacancyForTable:
    """Класс для удобного для вывода таблицы представления данных о вакансии.

        Attributes:
            name (str): Название вакансии
            salary (str): Строка с нижней и верхнец границами з\\п и валютой
            area_name (str): Город
            date (str): Дата публикации в полном формате
            premium (str): Премиум-вакансия или нет
            work_experience (str): Требуемый опыт работы
            description (str): Описание вакансии
            key_skills (List[str]): Навыки, необходимые для работы
            employer_name (str): Название компании-работодателя
    """

    def __init__(self, name: str, description: str, salary: str, key_skills: List[str], employer_name: str,
                 area_name: str,
                 premium: str, work_experience: List[str], date: str, **not_needed):
        """Инициализирует объект VacancyForTable. Принимает значения и сохраняет их без изменений.

                    Args:
                        name (str): Название вакансии
                        salary (str): Строка с нижней и верхнец границами з\\п и валютой
                        date (str): Дата публикации в полном формате
                        premium (str): Премиум-вакансия или нет
                        work_experience (str): Код требуемого опыта работу
                        description (str): Описание вакансии
                        key_skills (List[str]): Навыки, необходимые для работы
                        employer_name (str): Название компании-работодателя
                        area_name (str): Город
                """
        self.name = name
        self.description = description
        self.key_skills = key_skills
        self.work_experience = work_experience
        self.premium = premium
        self.employer_name = employer_name
        self.salary = salary
        self.area_name = area_name
        self.date = date


class Vacancy:
    """Класс для представления данных о вакансии.

        Attributes:
            name (str): Название вакансии
            salary (Salary): Финансовая информация о вакансии
            area_name (str): Город
            published_at (str): Дата публикации в полном формате
            year (str): Год публикации
            premium (str): Премиум-вакансия или нет
            experience_id (str): Код требуемого опыта работу
            description (str or None): Описание вакансии
            key_skills (List[str] or None): Навыки, необходимые для работы
            employer_name (str or None): Название компании-работодателя
        """

    def __init__(self, name: List[str], area_name: List[str], published_at: List[str], salary_from: List[str],
                 salary_to: List[str],
                 salary_currency: List[str], premium: List[str] = None, experience_id: List[str] = None,
                 description: List[str] = None,
                 key_skills: List[str] = None,
                 employer_name: List[str] = None, salary_gross: List[str] = None, **not_needed):
        """Инициализирует объект Vacancy. Принимает значения в виде массивов из одного элемента, и берет этот элемент.

            Args:
                name (List[str]): Название вакансии
                salary (Salary): Финансовая информация о вакансии
                area_name (List[str]): Город
                published_at (List[str]): Дата публикации в полном формате
                year (List[str]): Год публикации
                premium (List[str]): Премиум-вакансия или нет
                experience_id (List[str]): Код требуемого опыта работу
                description (List[str] or None): Описание вакансии
                key_skills (List[str] or None): Навыки, необходимые для работы
                employer_name (List[str] or None): Название компании-работодателя
                salary_from (List[str]): Нижняя граница з\\п
                salary_to (List[str]): Верхняя граница з\\п
                salary_currency (List[str]): Валюта
                salary_gross (List[str] or None): з\\п с учетом налогов или нет

            >>> type(Vacancy(['Препод'], ['Екб'], ['2022-12-01T00:00:00+0000'], ['10'], ['20'], ['RUR'])).__name__
            'Vacancy'
            >>> type(Vacancy(['Препод'], ['Екб'], ['2022-12-01T00:00:00+0000'], ['10'], ['20'], ['RUR']).salary).__name__
            'Salary'
            >>> Vacancy(['Препод'], ['Екб'], ['2022-12-01T00:00:00+0000'], ['10'], ['20'], ['RUR']).name
            'Препод'
            >>> type(Vacancy(['Препод'], ['Екб'], ['2022-12-01T00:00:00+0000'], ['10'], ['20'], ['RUR'],\
            ['True'], ['Опыт'], ['Описание'], ['Скилы'], ['URFU'], ['False']).key_skills).__name__
            'list'
        """
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

    def transform_for_table(self) -> VacancyForTable:
        """Преобразует объект Vacancy в удобный для печати объект VacancyForTable

            Returns:
                VacancyForTable: Преобразованная для таблицы вакансия

            >>> type(Vacancy(['Препод'], ['Екб'], ['2022-12-01T00:00:00+0000'], ['10'], ['20'], ['RUR'],\
            ['true'], ['noExperience'], ['Описание'], ['Скилы'], ['URFU'], ['false']).transform_for_table()).__name__
            'VacancyForTable'
            >>> Vacancy(['Препод'], ['Екб'], ['2022-12-01T00:00:00+0000'], ['10'], ['20'], ['RUR'],\
            ['true'], ['noExperience'], ['Описание'], ['Скилы'], ['URFU'], ['false']).transform_for_table().work_experience
            'Нет опыта'
            >>> Vacancy(['Препод'], ['Екб'], ['2022-12-01T00:00:00+0000'], ['10'], ['20'], ['RUR'],\
            ['true'], ['noExperience'], ['Описание'], ['Скилы'], ['URFU'], ['false']).transform_for_table().date
            '01.12.2022'
            >>> Vacancy(['Препод'], ['Екб'], ['2022-12-01T00:00:00+0000'], ['10'], ['20'], ['RUR'],\
            ['true'], ['noExperience'], ['Описание'], ['Скилы'], ['URFU'], ['false']).transform_for_table().premium
            'Да'
            >>> type(Vacancy(['Препод'], ['Екб'], ['2022-12-01T00:00:00+0000'], ['10'], ['20'], ['RUR'],\
            ['true'], ['noExperience'], ['Описание'], ['Скилы'], ['URFU'], ['false']).transform_for_table().salary).__name__
            'str'

        """
        premium = 'Да' if self.premium.lower() == 'true' else 'Нет'
        salary = self.salary.format_salary()
        work_experience = Translators.WorkExperience[self.experience_id].value
        date = self.__parse_date()

        return VacancyForTable(
            name=self.name,
            description=self.description,
            key_skills=self.key_skills,
            work_experience=work_experience,
            premium=premium,
            employer_name=self.employer_name,
            salary=salary,
            area_name=self.area_name,
            date=date
        )

    def __parse_date(self) -> str:
        """Превращает timestamp в строку формата {день.месяц.год}

            Returns:
                str: Строка формата {день.месяц.год}
        """
        year, month, day = self.published_at \
            .split('T')[0] \
            .split('-')
        return f'{day}.{month}.{year}'


class Translators:
    """Класс, предоставляющий Enum'ы и словари для конвертирования опыта и валюты

        Attributes:
            currency_to_rub Dict[str, int]: Ключ - валюта, значение - количество рублей в единице валюты
    """

    class WorkExperience(Enum):
        """Enum, переводящий код опыта в нормальную строку"""
        noExperience = "Нет опыта"
        between1And3 = "От 1 года до 3 лет"
        between3And6 = "От 3 до 6 лет"
        moreThan6 = "Более 6 лет"

    class WorkExperienceSorted(IntEnum):
        """IntEnum, предоставляет номер приоритетов опыта для сортировки"""
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
        """Enum, переводящий трехбуквенный код валюты в нормальную строку"""
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
    """Класс, предоставляющий различные методы, такие как методы для сортировки и фильтрации вакансий."""

    @staticmethod
    def filter(filter_name: str) -> Callable:
        """Возвращает функцию фильтрации, исходя из переданного столбца.

            Args:
                filter_name (str): Название столбца, который нужно отфильтровать

            Returns:
                Callable: Функция фильтрации данного столбца
        """
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
        """Функция, определяющая, является ли переданное название столбца столбцом таблицы.

            Args:
                key (str): Название столбца

            Returns:
                bool: Данный столбец есть в таблице
        """
        return key in ['Навыки', 'Оклад', 'Дата публикации вакансии', 'Опыт работы', 'Премиум-вакансия',
                       'Идентификатор валюты оклада', 'Название', 'Название региона', 'Компания', 'Описание']

    @staticmethod
    def sort_date(row: Vacancy):
        Utils.date1(row)
        Utils.date3(row)
        return Utils.date2(row)

    r = re.compile(r"[-T:]")

    @staticmethod
    def date1(row: Vacancy):
        (years, months, days, hours, minutes, seconds_and_diff) = re.split(Utils.r, row.published_at)
        seconds = int(seconds_and_diff[:2])
        plus = seconds_and_diff[3] == '+'
        diff = seconds_and_diff[4:]
        years = int(years) - 1970
        diffHours = int(diff[:1])
        diffMinutes = int(diff[2:])
        minutes = int(minutes)
        hours = int(hours)
        if plus:
            minutes += diffMinutes
            hours += diffHours
        else:
            minutes -= diffMinutes
            hours -= diffHours
        return years * 365 * 24 * 60 * 60 + int(months) * 30 * 24 * 60 * 60 + hours * 60 * 60 + minutes * 60 + int(
            seconds)

    @staticmethod
    def date2(row: Vacancy):
        return datetime.datetime.strptime(row.published_at,
                                          '%Y-%m-%dT%H:%M:%S%z').timestamp()

    @staticmethod
    def date3(row: Vacancy):
        return row.published_at

    @staticmethod
    def sort(sort_name: str) -> Callable:
        """Метод, возвращающий функцию сортировки переданного столбца.

            Args:
                sort_name (str): Название столбца

            Returns:
                Callable: Функция сортировки данного столбца
        """
        sorts = {
            'Навыки': lambda row: len(row.key_skills),
            'Оклад': lambda row: row.salary.get_middle_salary_rub(),
            'Дата публикации вакансии': Utils.sort_date,
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
    """Класс для вывода данных"""

    @staticmethod
    def get_vacs(grouped: groupby, by_year: bool = True, need_div: bool = True, default: Dict = None) -> Tuple[
        Dict[str, int], Dict[str, int]]:
        """Сортирует вакансии по количеству и по з\\п и возвращает соответствующие словари

            Args:
                grouped (Iterable): Сгруппированный по городу или году итератор вакансий
                by_year (bool): Да, если группировка по годам
                need_div (bool): Да, если нужно вычислять среднюю з\\п
                default (Dict): Значения, которые нужно добавить в начале. Используется для того, чтобы проставить года.

            Returns:
                Tuple[\n
                    Dict[str, int]: Словарь средних зарплат по городам (need_div = False => суммы зарплат)\n
                    Dict[str, int]: Словарь количества вакансий по городам\n
                ]
        """
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
    def clear_by_city(salary_by_city: Dict[str, int], vacancies_by_city: Dict[str, float], all_count: int) -> None:
        """Метод берет распределения зарплат и вакансий по городам. Вычисляет средние зарплаты по городам. Вычисляет
        долю вакансий из всех для каждого города. Города, у которых доля вакансий меньше 0.01 не учитываются

            Args:
                salary_by_city (Dict[str, int]): Суммарные зарплаты по городам
                vacancies_by_city (Dict[str, float]): Количество вакансий по городам
                all_count (int): Общее количество вакансий
        """
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
        """Декоратор. Возвращает функцию для вывода таблицы в консоль, если введено 'Вакансии', или функцию
        для создания файлов, если введено 'Статистика'

            Args:
                read_csv (Callable): функция, возвращающая итератор по вакансиям

            Returns:
                Callable: Функция для вывода данных по вакансиям
        """

        def table(self) -> None:
            """Печатает таблицу вакансий в консоль. Перед этим принимает с консоли параметры и проверяет
            их на валидность"""
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
            # prof.disable()
            if end is None:
                print(self._DataSet__table.get_string(start=start, fields=fields))
            else:
                print(self._DataSet__table.get_string(start=start, end=end, fields=fields))
            # prof.enable()

        def file(self, prof_name: str = None, file_name: str = None):
            """Создает файлы graph.png, report.pdf, report.xlsx в папке report."""
            csv_generator = read_csv(self) if file_name is None else read_csv(self, file_name)
            next(csv_generator)

            vacancies = [v for v in csv_generator]
            vacs_by_year = groupby(vacancies, lambda v: v.year)
            vacs_by_city = groupby(vacancies, lambda v: v.area_name)

            vacancies_with_prof = None
            profs_by_year = None
            professions_by_year, profs_salary_by_year = None, None

            vacancies_by_year, salary_by_year = InputConnect.get_vacs(vacs_by_year)
            if prof_name is not None:
                vacancies_with_prof = list(filter(lambda v: prof_name in v.name, vacancies))
                profs_by_year = groupby(vacancies_with_prof, lambda v: v.year)
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

            # print('Динамика уровня зарплат по годам:', salary_by_year)
            # print('Динамика количества вакансий по годам:', vacancies_by_year)
            # print('Динамика уровня зарплат по годам для выбранной профессии:', profs_salary_by_year)
            # print('Динамика количества вакансий по годам для выбранной профессии:', professions_by_year)
            # print('Уровень зарплат по городам (в порядке убывания):',
            # salary_by_city_to_print)
            # print('Доля вакансий по городам (в порядке убывания):',
            # vacancies_by_city_to_print)

            return salary_by_city_to_print, vacancies_by_city_to_print,\
                   salary_by_year, vacancies_by_year if prof_name is None else \
                salary_by_city_to_print, vacancies_by_city_to_print, salary_by_year,\
                   vacancies_by_year, profs_salary_by_year, professions_by_year, prof_name

        # prof.disable()

        # prof.enable()
        return file if to_show == 'Статистика' else table


class DataSet:
    """Класс, который может читать csv файлы с вакансиями и хранить данные о них.

        Attributes:
            file_name (str): Относительный путь к обрабатываемому файлу
            vacancies_objects (List[Vacancy]): Список считанных вакансий
    """

    to_show = None

    def __init__(self, _to_show: str):
        """Инициализирует объект DataSet."""
        self.file_name = None
        self.vacancies_objects: List[Vacancy] = []
        self.__RE_ALL_HTML = re.compile(r'<.*?>')
        self.__RE_ALL_NEWLINE = re.compile(r'\n|\r\n')
        self.__RE_WHITESPACES = re.compile(r'/\s\s+/')
        self.__header: List[str] = []
        self.__header_for_table = ['№', 'Название', 'Описание', 'Навыки',
                                   'Опыт работы', 'Премиум-вакансия', 'Компания',
                                   'Оклад', 'Название региона', 'Дата публикации вакансии']
        self.__table = PrettyTable(self.__header_for_table,
                                   max_width=20, align='l', hrules=1)
        self.to_show = _to_show

    @InputConnect.print_table
    def read_csv(self, file_name: str = None) -> Vacancy or []:
        """Генератор. Возвращает вакансии типа Vacancy для каждой строки из csv файла.

            Returns:
                Iterator[Vacancy]: Итератор по вакансиям из csv файла
        """
        # prof.disable()
        self.file_name = input('Введите название файла: ') if file_name is None else file_name
        # prof.enable()
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
                            sort_query: str, sort_reverse: bool) -> None:
        """Применяет требуемые фильтр и сортировку к списку вакансий и добавляет их в таблицу

            Args:
                fields (List[Vacancy]): Список вакансий
                filter_name (str): Поле, по которому идет фильтрация
                filter_value (str): Значение поля, по которому идет фильтрация
                sort_query (str): Поле, по которому идет сортировка
                sort_reverse (bool): Сортировка по возрастанию или убыванию
        """
        index = 0
        if filter_name != '':
            fields = list(filter(lambda x: Utils.filter(filter_name)(filter_value, x), fields))
        if sort_query != '':
            fields = sorted(fields, key=Utils.sort(sort_query), reverse=sort_reverse)
        fields = map(lambda v: v.transform_for_table(), fields)
        for field in fields:
            index += 1
            self.__table.add_row(
                [str(index)] + [self.__trim_row(self.__transform_skill(k, v)) for k, v in field.__dict__.items()])

    @staticmethod
    def __transform_skill(k: str, v: List[str]) -> str:
        """Возвращает поле 'key_skills', в котором навыки соединены по строкам, или само поле без изменений

            Args:
                k (str): Поле
                v (List[str]) Значение поля

            Returns:
                str: поле 'key_skills', в котором навыки соединены по строкам
        """
        return '\n'.join(v) if k == 'key_skills' else v

    @staticmethod
    def __trim_row(row: str) -> str:
        """Обрезает строку, если ее длина больше 100 и добавляет троеточие.

            Args:
                row (str): Строка, которую нужно сократить

            Returns:
                str: Строка не длиннее 100 символов + '...'

            >>> DataSet._DataSet__trim_row('Очень длинная строка Очень длинная строка Очень длинная строка Очень' +\
            'длинная строка Очень длинная строка Очень длинная строка')
            'Очень длинная строка Очень длинная строка Очень длинная строка Оченьдлинная строка Очень длинная стр...'
            >>> DataSet._DataSet__trim_row('Короткая строка')
            'Короткая строка'
        """
        return row if len(row) <= 100 else row[:100] + '...'

    def __get_inputs(self) -> (str, str, str, bool, int, int or None, List[str], str):
        """Берет с консоли параметры для сортировки и фильтрации, проверяет их на валидность, и возвращает их и
        сообщение об ошибке последним элементом, если параметры не валидные.

            Returns:
                tuple[\n
                str: Поле, по которому нужно провести фильтрацию\n
                str: Значение поля для фильтрации\n
                str: Поле, по которому нужно провести сортировку\n
                bool: Сортировка по возрастанию или нет\n
                int: Начальный индекс вакансий для показа\n
                int or None: Конечный индекс вакансий для показа или до конца\n
                List[str]: Столбцы, которые необходимо вывести\n
                str: Сообщение об ошибке\n
                ]
        """
        # prof.disable()
        filter_query = input('Введите параметр фильтрации: ')
        sort_query = input('Введите параметр сортировки: ')
        sort_reverse_query = input('Обратный порядок сортировки (Да / Нет): ')
        # prof.enable()
        sort_reverse = False if sort_reverse_query in ['Нет', ''] else True
        filter_name, filter_value, err_msg = self.__parse_query(filter_query)

        if not Utils.can_aggregate(sort_query) and sort_query != '':
            err_msg = 'Параметр сортировки некорректен'
        if sort_reverse_query not in ['Нет', 'Да', '']:
            err_msg = 'Порядок сортировки задан некорректно'
        # prof.disable()
        a1 = input('Введите диапазон вывода: ')
        a2 = input('Введите требуемые столбцы: ')
        # prof.enable()
        start, end = self.__prepend_rows(a1)
        fields = self.__prepend_fields(a2.split(', '))

        return filter_name, filter_value, sort_query, sort_reverse, start, end, fields, err_msg

    def __prepend_fields(self, fields: List[str]) -> List[str]:
        """Проверяет, что введенные столбцы есть в таблице, иначе ставит значение по умолчанию

            Args:
                fields (List[str]): Введенные столбцы

            Returns:
                List[str]: Столбцы для вывода
        """
        if fields[0] == '' or any(filter(lambda field: field not in self.__header_for_table, fields)):
            fields = self.__header_for_table
        else:
            fields.append('№')
        return fields

    def __prepend_rows(self, rows: str) -> (int, int or None):
        """Проверяет на валидность введенные начальную и конечную позицию для показа вакансий.
        Иначе возвращает стандартные значения

            Args:
                rows (str): Строка с начальной и конечной позициями через пробел

            Returns:
                tuple[\n
                    int: Начальная позиция\n
                    int or None: Конечная позиция, если она меньше длины таблицы\n
                ]
        """
        rows = rows.split(' ')
        start = 0
        end = None
        if len(rows) == 2:
            start = int(rows[0]) - 1
            end = int(rows[1]) - 1
        elif len(rows) == 1 and rows[0] != '':
            start = int(rows[0]) - 1

        return start, end

    def __parse_query(self, query: str) -> (str, str or List[str], str):
        """Проверяет на валидность введенный параметр фильтрации. Если нет, возвращает сообщение об
        ошибке последним аргументом

            Args:
                query (str): Введенная строка с параметром фильтрации вида '{Столбец}: {Значение1, Значение2, ...}'

            Returns:
                tuple[\n
                    str: Столбец для фильтрации\n
                    str: Значение столбца для фильтрации\n
                    str: Сообщение об ошибке\n
                ]

            >>> DataSet()._DataSet__parse_query("Направильный формат")
            ('', '', 'Формат ввода некорректен')
            >>> DataSet()._DataSet__parse_query("Не существующее поле: 100")
            ('', '', 'Параметр поиска некорректен')
            >>> DataSet()._DataSet__parse_query("Навыки: Первый, Второй, Третий")
            ('Навыки', ['Первый', 'Второй', 'Третий'], '')
            >>> DataSet()._DataSet__parse_query("Оклад: 100000")
            ('Оклад', '100000', '')
        """
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
        """Удаляет html теги и разделяет строки по \\n для всег полей вакансии и преобразует лист в поля для класса
        Vacancy

            Args:
                items (List[str]): Считанная строка с данными для вакансии

            Returns:
                Dict[str, List[str]]: Словарь с полями для создания объекта Vacancy
        """
        field = {}
        for column, row in zip(self.__header, items):
            field[column] = list(map(self.__delete_html, self.__split_by_newline(row)))
        return field

    def __delete_html(self, item: str) -> str:
        """Удаляет html теги из строки.

            Args:
                item (str): Строка, из которой нужно удалить html

            Returns:
                str: Очищенная строка
        """

        return " ".join(re.
                        sub(self.__RE_ALL_HTML, "", item)
                        .split())

    def __split_by_newline(self, item: str) -> List[str]:
        """Разделяет строку по спецсимволу \\n.

            Args:
                item (str): Строка для разделения

            Returns:
                List[str]: Список строк, разделенных по \n
        """
        return re.split(self.__RE_ALL_NEWLINE, item)

# reader = DataSet('Статистика')
# #prof.disable()
# prof_name = input('Введите название профессии: ')
# wkhtml_path = input('Введите путь до wkghml.exe или пустую строку для стандартного пути: ')
# #prof.enable()
# wkhtml_path = os.path.abspath(
#     r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe' if wkhtml_path == "" else wkhtml_path)
# rep = Report(*reader.read_csv(prof_name=prof_name))
# rep.generate_excel()
# rep.generate_image()
# rep.generate_pdf(wkhtml_path)

# prof.disable()
# prof.dump_stats('mystats.stats')
# with open('mystats_output.txt', 'wt') as output:
#     stats = Stats('mystats.stats', stream=output)
#     stats.sort_stats('cumulative', 'time')
#     stats.print_stats()
