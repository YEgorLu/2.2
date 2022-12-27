import pandas as pd
import sqlite3

con = sqlite3.connect('proj.db')
ALL_YEARS = range(2003, 2023)
prof_name = input('Введите название профессии: ')
font_dec = '\033[1m' + '\033[92m'
end_dec = '\033[0m'

# Датафрейм со статистикой по годам для профессии. Запросом отбираем вакансии с нужным именем, превращаем дуту ---------
# из формата YYYY-MM в YYYY, группируем по годам, считаем для года среднюю з\п и количество вакансий -------------------
df_prof = pd.read_sql(f"""SELECT STRFTIME('%Y', date || '-01') AS 'year',
 ROUND(AVG(salary)) AS 'mean', COUNT(salary) as 'count'
FROM VACANCY
WHERE name LIKE '%{prof_name}%'
GROUP BY YEAR
""", con=con, index_col='year')

# Заполняем нулями года, в которые профессии не было в вакансиях
for year in ALL_YEARS:
    y = str(year)
    if y not in df_prof.index:
        df_prof.loc[y] = 0
df_prof = df_prof.sort_index()
# ----------------------------------------------------------------------------------------------------------------------

# Датафрейм со статистикой по годам для профессии. Превращаем дату -----------------------------------------------------
# из формата YYYY-MM в YYYY, группируем по годам, считаем для года среднюю з\п и количество вакансий -------------------
df_year = pd.read_sql("""SELECT STRFTIME('%Y', date || '-01') AS 'year',
 ROUND(AVG(salary)) AS 'mean', COUNT(salary) as 'count'
FROM VACANCY
GROUP BY YEAR
""", con=con, index_col='year')
# ----------------------------------------------------------------------------------------------------------------------

# Датафрейм со статистикой з\п по городам. Группируем данные по городам, считаем средние з\п и количество вакансий, ----
# сортируем города по з\п. Отбираем топ10 городов, у которых вакансий более 0.01% --------------------------------------
df_city_salary = pd.read_sql(F"""SELECT area_name, avg FROM
(SELECT area_name, ROUND(AVG(salary)) AS 'avg', COUNT(salary) as 'count'
FROM VACANCY
GROUP BY area_name
ORDER BY avg DESC)
WHERE count > (SELECT COUNT(*) FROM VACANCY) * 0.01
LIMIT 10
""", con=con, index_col = 'area_name')
# ----------------------------------------------------------------------------------------------------------------------

# Датафрейм со статистикой количества вакансий по городам. Группируем данные по городам, считаем количество вакансий, --
# сортируем по количеству. Превращаем количество вакансий в долю вакансий с двумя знаками после запятой и берем топ10 --
df_city_count = pd.read_sql(F"""SELECT area_name,
  CAST(ROUND(CAST(count as REAL) / (SELECT COUNT(*) FROM VACANCY), 4) * 100 AS TEXT) || '%' as 'proc' FROM
(SELECT area_name, COUNT(salary) as 'count'
FROM VACANCY
GROUP BY area_name
ORDER BY count DESC)
LIMIT 10
""", con=con, index_col='area_name')
# ----------------------------------------------------------------------------------------------------------------------

print(font_dec + 'Датафрейм со статистикой по годам для профессии. mean - средняя з\п, count - кол-во вакансий' + end_dec)
print(df_prof)
print(font_dec + 'Датафрейм со статистикой по годам. mean - средняя з\п, count - кол-во вакансий' + end_dec)
print(df_year)
print(font_dec + 'Датафрейм со статистикой з\п по городам' + end_dec)
print(df_city_salary)
print(font_dec + 'Датафрейм со статистикой количества вакансий по городам' + end_dec)
print(df_city_count)