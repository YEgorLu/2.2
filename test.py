from unittest import TestCase
from main import Salary, Vacancy, DataSet


class SalaryTests(TestCase):
    salary = Salary(['10'], ['20'], ['RUR'], None)

    def test_salary_type(self):
        self.assertEqual(type(self.salary).__name__, 'Salary')

    def test_salary_salary_from(self):
        self.assertEqual(self.salary.salary_from, '10')

    def test_salary_salary_to(self):
        self.assertEqual(self.salary.salary_to, '20')

    def test_salary_salary_currency(self):
        self.assertEqual(self.salary.salary_currency, 'RUR')


class VacancyTests(TestCase):
    vacancy = Vacancy(['Препод'], ['Екб'], ['2022-12-01T00:00:00+0000'], ['10'], ['20'], ['RUR'],
                      ['True'], ['Опыт'], ['Описание'], ['Скилы'], ['URFU'], ['False'])

    def test_salary_salary_currency(self):
        self.assertEqual(type(self.vacancy).__name__, 'Vacancy')

    def test_vacancy_salary_type(self):
        self.assertEqual(type(self.vacancy.salary).__name__, 'Salary')

    def test_salary_simple_field(self):
        self.assertEqual(self.vacancy.name, 'Препод')

    def test_salary_key_skills_type(self):
        self.assertEqual(type(self.vacancy.key_skills).__name__, 'list')


class TransformForTableTests(TestCase):
    vacancy = Vacancy(['Препод'], ['Екб'], ['2022-12-01T00:00:00+0000'], ['10'], ['20'], ['RUR'],
                      ['true'], ['noExperience'], ['Описание'], ['Скилы'], ['URFU'], ['false'])

    def test_for_table_type(self):
        self.assertEqual(type(self.vacancy.transform_for_table()).__name__, 'VacancyForTable')

    def test_for_table_work_experience(self):
        self.assertEqual(self.vacancy.transform_for_table().work_experience, 'Нет опыта')

    def test_for_table_date(self):
        self.assertEqual(self.vacancy.transform_for_table().date, '01.12.2022')

    def test_for_table_premium(self):
        self.assertEqual(self.vacancy.transform_for_table().premium, 'Да')

    def test_for_table_salary_type(self):
        self.assertEqual(type(self.vacancy.transform_for_table().salary).__name__, 'str')


class TrimRowTests(TestCase):
    def test_long_str(self):
        self.assertEqual(
            DataSet()._DataSet__trim_row('Очень длинная строка Очень длинная строка Очень длинная строка Очень' + \
                                         'длинная строка Очень длинная строка Очень длинная строка'),
            'Очень длинная строка Очень длинная строка Очень длинная строка Оченьдлинная строка Очень длинная стр...')

    def test_short_str(self):
        self.assertEqual(DataSet()._DataSet__trim_row('Короткая строка'), 'Короткая строка')


class ParseQueryTests(TestCase):
    def test_wrong_format(self):
        self.assertEqual(DataSet()._DataSet__parse_query("Направильный формат"), ('', '', 'Формат ввода некорректен'))

    def test_incorrect_field(self):
        self.assertEqual(DataSet()._DataSet__parse_query("Не существующее поле: 100"), ('', '', 'Параметр поиска некорректен'))

    def test_key_skills(self):
        self.assertEqual(DataSet()._DataSet__parse_query("Навыки: Первый, Второй, Третий"), ('Навыки', ['Первый', 'Второй', 'Третий'], ''))

    def test_salary(self):
        self.assertEqual(DataSet()._DataSet__parse_query("Оклад: 100000"), ('Оклад', '100000', ''))