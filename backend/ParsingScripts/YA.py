import os
import time
import logging
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

SELENIUM_URL = os.environ.get("SELENIUM_URL")

import time
import random



def get_driver() -> WebDriver:
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    options.add_argument("--lang=ru-RU")
    options.add_argument("--window-size=1920,1080")



    return webdriver.Remote(
        command_executor=SELENIUM_URL,
        options=options
    )

# def get_local_driver() -> WebDriver:
#     options = Options()
#     options.add_argument('--headless=new')
#     options.add_argument('--disable-gpu')
#     options.add_argument('--no-sandbox')
#     options.add_argument('--disable-dev-shm-usage')

#     # options.binary_location = "C:\\Users\\mrWight\\AppData\\Local\\Google\\Chrome SxS\\Application\\chrome.exe"
#     # # service = Service(executable_path="chromedriver.exe")

#     return webdriver.Chrome(options=options)

def parse_ya_sync():
    driver = get_driver()
    try:
        driver.get("https://ya.ru")
        time.sleep(4)

        elements = driver.find_elements(By.CSS_SELECTOR, "section.informers3__stocks a.informers3__stocks-item")

        data = []
        for elem in elements:
            text = elem.text.strip()
            if text.startswith("USD"):
                rate = text.replace("USD", "").strip()
                data.append(("USD", rate))
            elif text.startswith("EUR"):
                rate = text.replace("EUR", "").strip()
                data.append(("EUR", rate))

        df = pd.DataFrame(data, columns=["Currency", "Rate"])
        return df
    except:
        raise RuntimeError("parsing failed")


    finally:
        driver.quit()


async def async_selenium():
    loop = asyncio.get_running_loop() 
    with ThreadPoolExecutor() as executor:
        df = await loop.run_in_executor(executor, parse_ya_sync)
    return df


async def parse_ya():
    df = await async_selenium()
    return df


# if __name__ == "__main__":
#     t = time.time()
#     df = asyncio.run(parse_ya())
#     print(df)
#     print(time.time()-t)

# тестовый парсер selenium абирает курс доллара с главной страницы яндекс