# parsing-manager

Централизованный менеджер для запуска парсеров, сбора данных из разных источников и экспорта результатов. Проект задуман как единая точка входа (REST API) для HTTP- и браузерных парсинговых задач, с удобной регистрацией новых парсеров и стандартными форматами выдачи.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-browser-43B02A?logo=selenium&logoColor=white)
![Requests](https://img.shields.io/badge/Requests-http-20232a)
![Pandas](https://img.shields.io/badge/Pandas-dataframe-150458?logo=pandas&logoColor=white)
![BeautifulSoup4](https://img.shields.io/badge/BS4-parse-4B275F)

> Программа позволяет централизованно собирать данные при помощи различных парсеров.

---

## Возможности

- Единый REST API для запуска и мониторинга парсинговых задач
- Поддержка двух подходов:
  - HTTP‑парсинг (requests/httpx + lxml/bs4)
  - Браузерный парсинг (Selenium)
- Экспорт результатов:
  - CSV / XLSX (pandas, openpyxl)
  - DOCX (python-docx), при необходимости — отчёты
- Простое подключение новых парсеров через единый контракт
- Логирование шагов, ошибок и метаданных запуска
- Асинхронные запросы к источникам (httpx) там, где это уместно

> В репозитории также есть вспомогательный сервис docTranstator (FastAPI) для работы с документами в форматах xls, doc и pdf
---

## Структура проекта

```
parsing-manager/
├─ backend/           # мендеджер
│  ├─ main.py         # FastAPI менеджера парсинга
│  ├─ ParsingScripts
│  │  ...                   # скрипты для парсинга
│  │  __init__.py           # регистрация нового парсера
├─ docTranstator/           # Вспомогательный сервис для работы с документами
│  ├─ main.py         #FastApi преобразование файлов
├─ frontend/
│  ├─ nginx.conf     # Конфигурация сервиса nginx для web страницы
```
---

## Быстрый старт (локально)

1) Клонируйте репозиторий:
```bash
git clone https://github.com/vanin2004/parsing-manager.git
cd parsing-manager
```
2) Запустите docker-compose

```bash
docker-compose up --buid
```
---

## Конфигурация

DOWNLOAD_DIR_VOLUME=/tmp/shared_downloads - хранилище старых данных сайтов в постоянной памяти
DOWNLOAD_DIR=/home/seluser/Downloads - хранилище файлов, которые скачиваются с сайтов
TZ=Europe/Moscow - временная зона для работы со временем
SELENIUM_URL=http://selenium:4444/wd/hub - url сервиса selenium для работы с браузером
DOCTRANSLATOR_URL=http://doctranslator:8001/convert - url сервиса конвертации устаревших расширений файлов
API_URL=http://backend:8000 - url api

Создайте файл `.env` в основной директории

---

## Как добавить новый парсер

1) Создайте модуль в `backend/parsers/your_parser.py`
2) Реализуйте функцию `run(params: dict) -> pandas.DataFrame | list[dict]`
3) Зарегистрируйте парсер в `__init__.py`
4) Добавьте схему валидации входных параметров (Pydantic)
5) Опишите парсер в README / docs, добавьте пример вызова

Это позволит вызывать парсер через API по его имени, а результат автоматически экспортировать в нужный формат.

---

