from typing import Dict
import requests
import xml.etree.ElementTree as ET

base_url = "http://www.cbr.ru/scripts/XML_daily.asp?date_req=01/"


def get_valutes(month: str, year: str) -> Dict[str, float]:
    """Отправляет запрос к серверу по первому числу указанного месяца и года

    :param month: Требуемый месяц
    :param year: Требуемый год
    :return: Словарь с ключами-месяцами. Значения - словари с кодом валюты как ключи
    """
    response = requests.get(base_url + month + '/' + year)
    r = ET.fromstring(response.content)
    valutes = {}
    for i in r.iter('Valute'):
        atts = {
            'value': [j.text for j in i.iterfind('Value')],
            'code': [j.text for j in i.iterfind('CharCode')],
            'n': [j.text for j in i.iterfind('Nominal')]
        }
        for k in atts:
            if atts[k][0] is not None:
                if k == 'value':
                    atts[k][0] = atts[k][0].replace(',', '.')
                atts[k] = atts[k][0]
            else:
                atts[k] = None

        valutes[atts['code']] = float(atts['value']) / int(atts['n'])
    return valutes

