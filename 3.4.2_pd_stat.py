import pandas as pd
import os.path as pt
import api.valutes as valutes
import os.path as pth
from matplotlib import pyplot as plt
from reportv2 import check_file
from jinja2 import Environment, FileSystemLoader
import pdfkit

# Получение имени csv, профессии, модуля wkhtml и их проверка ----------------------------------------------------------
file_name = pt.relpath(input('Введите название файла: '))
if not pt.exists(file_name):
    raise FileExistsError(f'Файла {file_name} не существует')
prof_name = input('Введите название проффесии: ')
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

# Отбираем вакансии по нужной профессии, группируем по годам и определяем средние зарплаты и количество вакансий за год
df_prof = df[df['name'].str.contains(prof_name, case=False)].reset_index(drop=True)
df_prof['date'] = df_prof['date'].str[:4]
prof_data = df_prof[['salary', 'date']].groupby('date').agg(['mean', 'count'])['salary']
prof_data['mean'] = prof_data['mean'].map(round)
# ----------------------------------------------------------------------------------------------------------------------

# Группируем все вакансии по годам и определяем средние зарплаты и количество вакансий за год --------------------------
df_data = df.reset_index(drop=True)
df_data['date'] = df_data['date'].str[:4]
final_df_data = df_data[['salary', 'date']].groupby('date').agg(['mean', 'count'])['salary']
final_df_data['mean'] = final_df_data['mean'].map(round)
# ----------------------------------------------------------------------------------------------------------------------

# Заполнение данных для таблицы с профессией по годам, в которых вакансий с профессией не было
prof_indexes = prof_data.index.tolist()
for year in final_df_data.index.tolist():
    if year not in prof_indexes:
        prof_data.loc[year] = 0
# ----------------------------------------------------------------------------------------------------------------------

# Создание графиков и их сохранение как pnd ----------------------------------------------------------------------------
fig, axs = plt.subplots(1, 2, layout='tight', figsize=[10, 5])
ax = axs[0]
ax.set_title('Уровень зарплат по годам', fontsize=20)
y_pos = range(final_df_data.shape[0])
years = final_df_data.index.tolist()
_salary_by_year = list(final_df_data['mean'].tolist())
prof_salary = list(prof_data['mean'].sort_index().tolist())
overall = ax.bar(y_pos, _salary_by_year, width=0.3)
prof = ax.bar(list(map(lambda x: x + 0.3, y_pos)), prof_salary, width=0.3)
ax.set_xticks(list(map(lambda x: x + 0.15, y_pos)), labels=years, rotation="vertical", fontsize=8)
for tick in ax.get_yticklabels():
    tick.set_fontsize(8)
ax.legend([overall, prof], [r'средняя з\п', r'з\п ' + prof_name], fontsize=8)
ax.grid(axis='y')

ax = axs[1]
y_pos = range(final_df_data.shape[0])
years = list(final_df_data.index.tolist())
salary_by_year = list(final_df_data['count'].tolist())
prof_salary = list(prof_data['count'].sort_index().tolist())
overall = ax.bar(y_pos, salary_by_year, width=0.3)
prof = ax.bar(list(map(lambda x: x + 0.3, y_pos)), prof_salary, width=0.3)
ax.set_xticks(list(map(lambda x: x + 0.15, y_pos)), labels=years, rotation="vertical", fontsize=8)
for tick in ax.get_yticklabels():
    tick.set_fontsize(8)
ax.legend([overall, prof], ['Количество вакансий', 'Количество ваканисий\n' + prof_name], fontsize=8)
ax.set_title('Количество вакансий по годам', fontsize=20)
ax.grid(axis='y')

save_path = pth.relpath(pth.join('report', 'year_graph.png'))
if check_file('png', save_path):
    plt.savefig(save_path)
# ----------------------------------------------------------------------------------------------------------------------

# Создание pdf с графиками и таблицей ----------------------------------------------------------------------------------
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('template/template_lite.html')

years_df = final_df_data
years_df['year'] = final_df_data.index
years_df['prof_salary'] = prof_data['mean']
years_df['prof_count'] = prof_data['count']
years_df = years_df[['year', 'mean', 'prof_salary', 'count', 'prof_count']]
years_table = years_df.to_numpy().tolist()
years_table_header = ['Год', 'Средняя зарплата', f'Средняя зарплата - {prof_name}', 'Количество вакансий',
               f'Количество вакансий - {prof_name}']

pdf_template = template.render({
    'first_table': years_table,
    'first_table_header': years_table_header,
    'prof_name': prof_name,
    'to_css': pth.abspath(pth.join('template', 'style.css')),
    'to_img': pth.abspath(pth.join('report', 'year_graph.png'))
})
config = pdfkit.configuration(wkhtmltopdf=wkhtml_path)
save_path = pth.normpath(pth.join('report', 'year_report.pdf'))
if check_file('pdf', save_path):
    pdfkit.from_string(pdf_template, save_path, configuration=config,
                       options={"enable-local-file-access": ""})
# ----------------------------------------------------------------------------------------------------------------------
