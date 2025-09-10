from . import SBIS
from . import KONTUR
from . import YA
from typing import Callable, Awaitable
import pandas as pd
import datetime
import asyncio
import enum

# при добавлении нового парсера необходимо добавить его в ParserKey и в parsers
class ParserKey:
    SBIS = "SBIS"
    KONTUR = "KONTUR"
    YA = "YA"

class ParserType(str, enum.Enum):
    SELENIUM = "selenium" # не могут работать параллельно, т.к. используют один и тот же экземпляр браузера
    HTTPX = "httpx" # несколько httpx парсеров могут работать параллельно с разными сайтами

class Parser:
    def __init__(self, 
                 key: str,
                 name: str, 
                 run: Callable[[], Awaitable[pd.DataFrame]], 
                 type: str = "", 
                 output_path: str = "",
                 latest_parse_datetime: datetime.datetime = None,
                 latest_parse_file_name: str = ""
                 ):
        self.key = key
        self.name = name
        self.run = run
        self.type = type
        self.output_path = output_path
        self.latest_parse_datetime = latest_parse_datetime
        self.latest_parse_file_name = latest_parse_file_name
        self.lock = asyncio.Lock()

    def get_lock(self) -> asyncio.Lock:
        return self.lock
    
    def get_key(self) -> str:
        return self.key

    def get_name(self) -> str:
        return self.name

    def get_run(self) -> Callable[[], Awaitable[pd.DataFrame]]:
        return self.run

    def get_type(self) -> str:
        return self.type

    def get_output_path(self) -> str:
        return self.output_path

    def get_latest_parse_datetime(self) -> datetime.datetime:
        return self.latest_parse_datetime

    def get_latest_parse_file_name(self) -> str:
        return self.latest_parse_file_name
    
    def set_latest_parse_file_name(self, path: str):
        self.latest_parse_file_name = path

    def set_latest_parse_date_time(self, date_time: datetime.datetime):
        self.latest_parse_datetime = date_time 

parsers_lock = asyncio.Lock()

parsers = {
    ParserKey.SBIS: Parser(
        key=ParserKey.SBIS,
        name="sbis.ru",
        run=SBIS.parse_sbis,
        type=ParserType.HTTPX,
        output_path="./oldData/SBIS/"
    ),
     ParserKey.KONTUR: Parser(
        key=ParserKey.KONTUR,
        name="kontur.ru",
        run=KONTUR.parse_kontur,
        type=ParserType.SELENIUM,
        output_path="./oldData/KONTUR/"

    ),
     ParserKey.YA: Parser(
        key=ParserKey.YA,
        name="ya.ru",
        run=YA.parse_ya,
        type=ParserType.SELENIUM,
        output_path="./oldData/YA/"
    )
}

