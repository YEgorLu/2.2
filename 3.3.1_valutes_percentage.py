import pandas as pd
import api.valutes as valutes

df = pd.read_csv('vacancies_dif_currencies.csv')
currencies = df.salary_currency.dropna()
grouped = df.groupby('salary_currency').agg(['count'])
sum_all = grouped['published_at'].sum()
percentage = grouped.drop(index=['AZN', 'GEL', 'KGS', 'UZS']).published_at / sum_all
percentage.to_csv('valutes_percentage.csv')