import requests
import concurrent.futures as cf
import csv


base_URI = "https://api.hh.ru/"
header = {'User-Agent': 'URFU_my_app'}


def transform_vac(vac):
    """
    Оставляет у вакансии только нужные поля
    :param vac: Вакансия из запроса по api
    :return:
    """
    salary_from = vac['salary']['from'] if vac['salary'] is not None else None
    salary_to = vac['salary']['to'] if vac['salary'] is not None else None
    salary_currency = vac['salary']['currency'] if vac['salary'] is not None else None
    area_name = vac['area']['name'] if vac['area'] is not None else None

    return {
        'name': vac['name'],
        'salary_from': salary_from,
        'salary_to': salary_to,
        'salary_currency': salary_currency,
        'area_name': area_name,
        'published_at': vac['published_at']
    }


def get_vacs_in_day(month: str or int, day: str or int):
    """
    Возвращает выгрузку вакансий за день
    :param day: День в двухзначном формате
    :param month: Месяц в двухзначном формате
    :return: Список вакансий
    """
    day = str(day)
    month = str(month)
    if len(day) == 1:
        day = '0' + day
    if len(month) == 1:
        month = '0' + month

    res = []
    date = '2022-'+ month + '-' + day
    i, j = 0, 2
    while (j < 25):
        data = get_vacs_from_hours(date, i, j)
        if data is not None:
            res += data
        i = i + 2
        j = j + 2




    # res = requests.get(base_URI + "vacancies",
    #                    params={'date_from': '2022-'+ month + '-' + day + 'T00:00:00+0000',
    #                            'date_to': '2022-'+ month + '-' + day + 'T23:59:59+0000',
    #                            'specialization': 1},
    #                    headers=header)

    return res


def get_vacs_from_hours(date: str, hour_from: str, hour_to: str):
    """
    Делаем запрос по вакансиям по одному часовому диапазону
    :param date: Год, месяц и день
    :param hour_from:
    :param hour_to:
    :return: Список вакансий
    """
    hour_from = str(hour_from)
    hour_to = str(hour_to)
    if len(hour_from) == 1:
        hour_from = '0' + hour_from
    if len(hour_to) == 1:
        hour_to = '0' + hour_to


    res = requests.get(base_URI + "vacancies",
                       params={'date_from': date + f'T{hour_from}:00:00+0000',
                               'date_to': date + f'T{hour_to}:00:00+0000',
                               'specialization': 1},
                       headers=header)
    if not res.ok:
        return None
    res = res.json()
    found = res['found']
    pages = res['pages']
    if found == 0:
        return None
    if pages == 0:
        return list(map(transform_vac, res['items']))

    if 'items' not in res:
        return None
    vacs = []

    with cf.ProcessPoolExecutor() as executor:
        futures = [executor.submit(get_vacs_from_pages, date + f'T{hour_from}:00:00+0000', date + f'T{hour_to}:00:00+0000', page) for page in range(pages)]

        for future in cf.as_completed(futures, timeout=None):
            data = future.result()
            if data is not None:
                vacs += future.result()

    return vacs


def get_vacs_from_pages(date_from: str, date_to: str, page: int):
    """
    Делаем запрос по вакансиям в одном часовом диапазоне к одной странице
    :param date_from:
    :param date_to:
    :param page: Номер страницы
    :return: Список вакансий
    """
    res = requests.get(base_URI + "vacancies",
                       params={'date_from': date_from,
                               'date_to': date_to,
                               'page': page,
                               'specialization': 1},
                       headers=header)
    res = res.json()

    if 'items' not in res:
        return None
    return list(map(transform_vac, res['items']))


if __name__ == '__main__':
    d = get_vacs_in_day(12, 21)
    print(d)
    print(len(d))
    header = ['name', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at']
    with open('hh.csv', 'w', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
        for row in d:
            writer.writerow(row)
