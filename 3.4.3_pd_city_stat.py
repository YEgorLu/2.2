import pandas as pd
import api.valutes as valutes
import os.path as pth
from matplotlib import pyplot as plt
import re
from reportv2 import check_file
from jinja2 import Environment, FileSystemLoader
import pdfkit
import concurrent.futures as cf

# Получение имени csv, профессии, модуля wkhtml и их проверка ----------------------------------------------------------
file_name = pth.relpath(input('Введите название файла: '))
if not pth.exists(file_name):
    raise FileExistsError(f'Файла {file_name} не существует')
prof_name = input('Введите название проффесии: ')
region_name = input('Введите название региона: ')
wkhtml_path = input('Введите путь до wkghml.exe или пустую строку для стандартного пути: ')
wkhtml_path = pth.abspath(
    r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe' if wkhtml_path == "" else wkhtml_path)
# ----------------------------------------------------------------------------------------------------------------------

# Проверка csv на формат данных ----------------------------------------------------------------------------------------
header = ['name', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at']
df = pd.read_csv(file_name)
columns = df.columns.tolist()
if len(header) != len(columns):
    raise SyntaxError('Файл имеет неверный формат')
for column in columns:
    if column not in header:
        raise SyntaxError('Файл имеет неверный формат')
# ----------------------------------------------------------------------------------------------------------------------

# Очистка пропущенных данных -------------------------------------------------------------------------------------------
df = df.dropna(subset=['name', 'salary_currency', 'area_name', 'published_at']) \
    .dropna(subset=['salary_from', 'salary_to'], how='all').reset_index(drop=True)
# ----------------------------------------------------------------------------------------------------------------------

# Выделение даты в формате yyyy-mm -------------------------------------------------------------------------------------
df['date'] = df['published_at'].str[:7]
# ----------------------------------------------------------------------------------------------------------------------

# Получение курсов валют на каждую представленную дату -----------------------------------------------------------------
currs = {}
for date in df['date'].unique():
    year = date[:4]
    month = date[5:7]
    currs[date] = valutes.get_valutes(month, year)
# ----------------------------------------------------------------------------------------------------------------------

def multiply_currency(row):
    """
    Переводит сумму в рубли.
    :param row: Строка из dataframe
    :return: Сумма в рублях или None, если валюта не отслеживалась на указанную дату
    """
    if row['salary_currency'] == 'RUR':
        return row['salary']

    if row['salary_currency'] not in currs[row['date']]:
        return None
    val = currs[row['date']][row['salary_currency']]
    return row['salary'] * val


# Переводим поля с salary в единую колонку с суммой в рублях -----------------------------------------------------------
df['salary'] = df[['salary_from', 'salary_to']].mean(axis=1)
df['salary'] = df.apply(axis=1, func=multiply_currency)
df = df[['name', 'salary', 'area_name', 'published_at', 'date']]
# ----------------------------------------------------------------------------------------------------------------------

# Отбор вакансий с подходящими prof_name и region_name, подсчет средней з\п и количества за года -----------------------
df_prof_area = df[df.name.str.contains(prof_name) & df.area_name.str.contains(region_name)].reset_index(
    drop=True)
df_prof_area['year'] = df_prof_area['date'].str[:4]
df_prof_area = df_prof_area[['salary', 'year']]
prof_area = df_prof_area.groupby('year').agg(['mean', 'count'])['salary']
prof_area['mean'] = prof_area['mean'].map(round)
for year in df['date'].str[:4].unique():
    if year not in prof_area.index:
        prof_area.loc[year] = 0
prof_area = prof_area.sort_index()
# ----------------------------------------------------------------------------------------------------------------------

# Подсчет средней з\п и количества вакансий по городам, составление топ10 городов --------------------------------------
df_area = df[['salary', 'area_name']].groupby('area_name').agg(['mean', 'count'])['salary'].dropna()
df_area['mean'] = df_area['mean'].map(round)
count_sum = df_area['count'].sum()
df_area['count'] = df_area['count'] / count_sum
df_area = df_area[df_area['count'] > 0.01]
top_salary = df_area[['mean']].sort_values(by='mean', ascending=False).iloc[:10]
top_count = df_area[['count']].sort_values(by='count', ascending=False).iloc[:10]
# ----------------------------------------------------------------------------------------------------------------------

# Создание графиков ----------------------------------------------------------------------------------------------------
fig, axs = plt.subplots(1, 2, layout='tight', figsize=[10, 5])

# Круговая диаграмма
ax = axs[1]
data = {'Другие': 1 - top_count['count'].sum(), **{city: top_count['count'].loc[city] for city in top_count.index}}
ax.pie(list(data.values()), labels=list(data.keys()), textprops={'fontsize': 6})
ax.set_title('Доля вакансий по городам', fontsize=20)

# Горизонтальная диаграмма
ax = axs[0]
y_pos = range(len(top_salary.index.tolist()))
cities = top_salary.index.tolist()
for i, city in enumerate(cities):
    cities[i] = re.sub(r'([- ])', lambda s: '-\n' if s.group(0) == '-' else '\n', city)
salary = top_salary['mean'].values.tolist()
ax.barh(y_pos, salary)
ax.set_yticks(y_pos, labels=cities, fontsize=6)
for tick in ax.get_xticklabels():
    tick.set_fontsize(8)
    tick.ha = 'right'
    tick.va = 'center'
ax.invert_yaxis()
ax.set_title('Уровень зарплат по городам', fontsize=20)
ax.grid(axis='x')

save_path = pth.relpath(pth.join('report', 'city_graph.png'))
if check_file('png', save_path):
    plt.savefig(save_path)
# ----------------------------------------------------------------------------------------------------------------------

# Создание pdf с графиками и таблицей ----------------------------------------------------------------------------------
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('template/template_city.html')

area_prof_table = prof_area
area_prof_table['year'] = prof_area.index
area_prof_table = area_prof_table[['year', 'mean', 'count']]

area_salary_table = top_salary
area_salary_table['area'] = top_salary.index
area_salary_table = area_salary_table[['area', 'mean']]

area_count_table = top_count
area_count_table['area'] = top_count.index
area_count_table['count'] = area_count_table['count'].map(lambda x:"{:.2f}%".format(x * 100).replace('.', ','))
area_count_table = area_count_table[['area', 'count']]

years_table_header = ['Год', 'Средняя зарплата', 'Количество вакансий']
city_salary_header = ['Город', 'Уровень зарплат']
city_count_header = ['Город', 'Доля вакансий']

pdf_template = template.render({
    'first_table': area_prof_table.to_numpy().tolist(),
    'first_table_header': years_table_header,
    'second_table': area_salary_table.to_numpy().tolist(),
    'second_table_header': city_salary_header,
    'third_table': area_count_table.to_numpy().tolist(),
    'third_table_header': city_count_header,
    'prof_name': prof_name,
    'area_name': region_name,
    'to_css': pth.abspath(pth.join('template', 'style.css')),
    'to_img': pth.abspath(pth.join('report', 'city_graph.png'))
})
config = pdfkit.configuration(wkhtmltopdf=wkhtml_path)
save_path = pth.normpath(pth.join('report', 'city_report.pdf'))
if check_file('pdf', save_path):
    pdfkit.from_string(pdf_template, save_path, configuration=config,
                       options={"enable-local-file-access": ""})
# ----------------------------------------------------------------------------------------------------------------------
