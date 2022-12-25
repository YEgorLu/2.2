import pandas as pd
import api.valutes as valutes


def get_salary(row):
    if row['salary_currency'] not in dic_valutes[row['date']]:
        return None
    return float(dic_valutes[row['date']][row['salary_currency']])
df = pd.read_csv('vacancies_dif_currencies.csv')
df['date'] = df['published_at'].str[:7]
df_valutes = df[['salary_currency', 'date']].dropna()

dic_valutes = {}
for date in df_valutes.date.unique():
    year, month = date.split('-')
    res = valutes.get_valutes(month, year)
    dic_valutes[date] = res

df_valutes['salary'] = df_valutes.apply(func=get_salary, axis=1).dropna()
final = df_valutes.reset_index().groupby(['date', 'salary_currency'])['salary'].aggregate('first').unstack()
final = final[['BYR', 'USD', 'EUR', 'KZT', 'UAH']]
final.to_csv('3.3.1_dataframe.csv')