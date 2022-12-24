import concurrent.futures as cf
import os
import pandas as pd
import api.valutes as valutes

def mutate_csv(file_name: str):
    def multiply_currency(row):
        if row['salary_currency'] == 'RUR':
            return row['salary']
        month = row['published_at'][5:7]
        if row['salary_currency'] not in valutis[month]:
            return None
        val = valutis[month][row['salary_currency']]
        return row['salary'] * val

    df = pd.read_csv(file_name)
    df = df.dropna(subset=['name', 'salary_currency', 'area_name', 'published_at']) \
        .dropna(subset=['salary_from', 'salary_to'], how='all').reset_index(drop=True)
    valutis = {}
    year = df['published_at'].iloc[0][:4]
    dates = df['published_at'].str[5:7]
    for month in dates.unique():
        valutis[month] = valutes.get_valutes(month, year)
    df['salary'] = df[['salary_from', 'salary_to']].mean(axis=1)
    df['salary'] = df.apply(axis=1, func=multiply_currency)
    df = df[['name', 'salary', 'area_name', 'published_at']]
    rel_name = os.path.basename(file_name)
    p = os.path.relpath(os.path.join('muted_csvs', rel_name))
    df.to_csv(p, index=False)
    return True

if __name__ == "__main__":
    with cf.ProcessPoolExecutor() as executor:
        files = []
        csvs_dir = input('Путь до папки с csv: ')
        for file in os.listdir(os.path.join('.', csvs_dir)):
            files.append(os.path.join('.', csvs_dir, file))

        futures = [executor.submit(mutate_csv, file_name) for file_name in files]
        output = []
        i = 0
        for future in cf.as_completed(futures, timeout=None):
            print(i)
            i+=1