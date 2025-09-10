import httpx
import json
import pandas as pd
import random
import asyncio


async def make_saby_request(region_code="57", duration=12, parent_contract=None, contractor_of_invoice=None, httpxClient = None):
    url = "https://saby.ru/service/?x_version=25.3200-58"

    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate",
        "accept-language": "ru-RU;q=0.8,en-US;q=0.5,en;q=0.3",
        "content-type": "application/json; charset=UTF-8",
        "dnt": "1",
        "origin": "https://saby.ru",
        "priority": "u=1, i",
        "referer": "https://saby.ru/tariffs?tab=ereport",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "x-calledmethod": "UslugaDogovora.GetContractServices",
        "x-originalmethodname": "0KPRgdC70YPQs9Cw0JTQvtCz0L7QstC+0YDQsC5HZXRDb250cmFjdFNlcnZpY2Vz",
        "x-requested-with": "XMLHttpRequest"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "protocol": 7,
        "method": "УслугаДоговора.GetContractServices",
        "params": {
            "ContractId": None,
            "ClientContractorOfTariffChange": None,
            "FixationThemes": None,
            "AdditionalParameters": {
                "d": [parent_contract, duration, region_code, contractor_of_invoice],
                "s": [
                    {"t": "Число целое", "n": "ParentContract"},
                    {"t": "Число целое", "n": "Duration"},
                    {"t": "Строка", "n": "RegionCode"},
                    {"t": "Число целое", "n": "ContractorOfInvoice"}
                ],
                "_type": "record",
                "f": 0
            }
        },
        "id": 1
    }
    
    cookies = {
        "lang": "ru",
        "DeviceId": "e6d8f32a-bd30-43ed-81d6-f826b518f467",
    }
    
    try:
        response = await httpxClient.post(
            url,
            headers=headers,
            json=payload,
            cookies=cookies,
            timeout=30
        )
        response.encoding = 'utf-8'
        response.raise_for_status()

        print(response.text[:100])
        
        return response.json()
        
    except httpxClient.exceptions.RequestException as e:
        print(f"Ошибка при отправке запроса: {e}")
        print(str(e))
        return None
    except json.JSONDecodeError as e:
        print(f"Ошибка при парсинге JSON ответа: {e}")
        return None

async def get_saby_tariffs_for_region(region_code,client):

    print(f"Получение тарифов для региона {region_code}...")
    
    result = await make_saby_request(region_code=region_code, httpxClient=client)
    
    if result:
        if "result" in result:
            return result["result"]
        else:
            print(f"Неожиданный формат ответа: {result}")
            return None
    else:
        print(f"Не удалось получить данные для региона {region_code}")
        return None

async def get_saby_tariffs_for_regions():
    async with httpx.AsyncClient() as client:
        regions = regions = {
    '77': 'Москва',
    '78': 'Санкт-Петербург',
    '01': 'Республика Адыгея',
    '02': 'Республика Башкортостан',
    '03': 'Республика Бурятия',
    '04': 'Республика Алтай',
    '05': 'Республика Дагестан',
    '06': 'Республика Ингушетия',
    '07': 'Респ. Кабардино-Балкария',
    '08': 'Республика Калмыкия',
    '09': 'Респ. Карачаево-Черкессия',
    '10': 'Республика Карелия',
    '11': 'Республика Коми',
    '12': 'Республика Марий Эл',
    '13': 'Республика Мордовия',
    '14': 'Республика Саха (Якутия)',
    '15': 'Северная Осетия - Алания',
    '16': 'Республика Татарстан',
    '17': 'Республика Тыва',
    '18': 'Удмуртская Республика',
    '19': 'Республика Хакасия',
    '20': 'Республика Чечня',
    '21': 'Республика Чувашия',
    '22': 'Алтайский край',
    '23': 'Краснодарский край',
    '24': 'Красноярский край',
    '25': 'Приморский край',
    '26': 'Ставропольский край',
    '27': 'Хабаровский край',
    '28': 'Амурская обл.',
    '29': 'Архангельская обл.',
    '30': 'Астраханская обл.',
    '31': 'Белгородская обл.',
    '32': 'Брянская обл.',
    '33': 'Владимирская обл.',
    '34': 'Волгоградская обл.',
    '35': 'Вологодская обл.',
    '36': 'Воронежская обл.',
    '37': 'Ивановская обл.',
    '38': 'Иркутская обл.',
    '39': 'Калининградская обл.',
    '40': 'Калужская обл.',
    '41': 'Камчатский край',
    '42': 'Кемеровская обл.',
    '43': 'Кировская обл.',
    '44': 'Костромская обл.',
    '45': 'Курганская обл.',
    '46': 'Курская обл.',
    '47': 'Ленинградская обл.',
    '48': 'Липецкая обл.',
    '49': 'Магаданская обл.',
    '50': 'Московская обл.',
    '51': 'Мурманская обл.',
    '52': 'Нижегородская обл.',
    '53': 'Новгородская обл.',
    '54': 'Новосибирская обл.',
    '55': 'Омская обл.',
    '56': 'Оренбургская обл.',
    '57': 'Орловская обл.',
    '58': 'Пензенская обл.',
    '59': 'Пермский край',
    '60': 'Псковская обл.',
    '61': 'Ростовская обл.',
    '62': 'Рязанская обл.',
    '63': 'Самарская обл.',
    '64': 'Саратовская обл.',
    '65': 'Сахалинская обл.',
    '66': 'Свердловская обл.',
    '67': 'Смоленская обл.',
    '68': 'Тамбовская обл.',
    '69': 'Тверская обл.',
    '70': 'Томская обл.',
    '71': 'Тульская обл.',
    '72': 'Тюменская обл.',
    '73': 'Ульяновская обл.',
    '74': 'Челябинская обл.',
    '75': 'Забайкальский край',
    '76': 'Ярославская обл.',
    '79': 'Еврейская АО',
    '83': 'Ненецкий АО',
    '86': 'Ханты-Мансийский АО',
    '87': 'Чукотский АО',
    '89': 'Ямало-Ненецкий АО',
    '90': 'Запорожская обл.',
    '91': 'Республика Крым',
    '92': 'Севастополь',
    '93': 'Донецкая нар. респ.',
    '94': 'Луганская нар. респ.',
    '95': 'Херсонская обл.'
}
        
        tariff_to_code = {
    "EOpSBISfrmLIoN": "отчетность легкий ип",
    "EOpSBISfrmLB2o": "отчетность легкий бюджет",
    "EOpSBISfrmLUo": "отчетность усн ",
    "EOpSBISfrmLO2oN": "отчетность осно",

    "EOpSBISfrmIoN": "отчетность базовый",
    "EOpSBISfrmB2o": "отчетность базовый бюджет",
    "EOpSBISfrmUo": "отчетность базовый усн",
    "EOpSBISfrmO2oN": "отчетность базовый осно",

    "EOpNull": "отчетность нулевка",

    "EOpSBISfrmUPQ12": "уполномоченная бухгалтерия подключение",
    "EOussvMin": "уполномоченная бухгалтерия за квартал"
    }
        
        all_tariffs = {}

        for region_id in regions:
            await asyncio.sleep(random.randint(1,5))
            region_tariffs = await get_saby_tariffs_for_region(region_id,client)

            if region_tariffs:
                tariffs = json.loads(region_tariffs)

                tariffs = [
                    {
                        "name": tariff_to_code[x["nomenclature"]],
                        "price": x["price"]
                    }
                    for x in tariffs["data"] if x["nomenclature"] in tariff_to_code
                ]
                all_tariffs[regions[region_id]] = tariffs
        
        return all_tariffs

def safe_extract(prices, substrings):
    for name in prices:
        for s in substrings:
            if s in name["name"].lower():
                return int(name["price"])
    return None

def json_to_df(data):
    rows = []
    for idx, (region_name, services) in enumerate(data.items(), start=1):
        prices = services

        rows.append({
            "Код региона": idx,
            "Название региона": region_name,
            "Тариф": "Легкий",
            "ИП": safe_extract(prices, ["легкий ип"]),
            "Бюджет": safe_extract(prices, ["легкий бюджет"]),
            "УСН": safe_extract(prices, ["усн "]),
            "ОСНО": safe_extract(prices, ["осно"]) if not safe_extract(prices, ["базовый осно"]) else None
        })

        rows.append({
            "Код региона": idx,
            "Название региона": region_name,
            "Тариф": "Базовый",
            "ИП": safe_extract(prices, ["базовый"]),
            "Бюджет": safe_extract(prices, ["базовый бюджет"]),
            "УСН": safe_extract(prices, ["базовый усн"]),
            "ОСНО": safe_extract(prices, ["базовый осно"]),
        })

        rows.append({
            "Код региона": idx,
            "Название региона": region_name,
            "Тариф": "Нулевка или ИП без сотрудников",
            "ИП": safe_extract(prices, ["нулевка"]),
            "УСН": None,
            "ОСНО": None,
            "Бюджет": None
        })

    return pd.DataFrame(rows)

async def parse_sbis():
    all_tariffs = await get_saby_tariffs_for_regions()
    return json_to_df(all_tariffs)