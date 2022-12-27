import sqlite3
import pandas as pd


df = pd.read_csv('3.3.1_dataframe.csv')
conn = sqlite3.connect('proj.db')
cur = conn.cursor()
df.to_sql('VALUTE', con=conn, index=False, if_exists='replace')


