import pandas as pd
import os.path
import sqlite3


def multiply_currency(row):
    if row['salary_currency'] == 'RUR':
        return round(row['salary'])
    cur.execute(f"""SELECT * FROM VALUTE WHERE DATE = '{row['date']}'""")
    valutes = dict(zip([col[0] for col in cur.description], cur.fetchone()))
    if row['salary_currency'] not in valutes or valutes[row['salary_currency']] is None:
        return None
    return round(row['salary'] * valutes[row['salary_currency']])


df = pd.read_csv('vacancies_dif_currencies.csv')
df = df.dropna(subset=['name', 'salary_currency', 'area_name', 'published_at']) \
    .dropna(subset=['salary_from', 'salary_to'], how='all').reset_index(drop=True)
con = sqlite3.connect('proj.db')
cur = con.cursor()

df['date'] = df['published_at'].str[:7]
df['salary'] = df[['salary_from', 'salary_to']].mean(axis=1)
df['salary'] = df.apply(axis=1, func=multiply_currency)
df = df[['name', 'salary', 'area_name', 'date']].dropna()
rel_name = os.path.basename('muted_vacancies_dif_currencies.csv')
conn = sqlite3.connect('proj.db')
df.to_sql('VACANCY', con=conn, index=True, if_exists='append')
