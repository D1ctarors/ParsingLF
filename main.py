import datetime
import requests
from bs4 import BeautifulSoup
import time
import fake_useragent
from random import randrange
import json
# from tqdm import tqdm
# from tqdm.asyncio import tqdm
# from progress.bar import Bar
import asyncio
import aiohttp


""" TODO
На получение и запись 10 страниц уйдёт ~21.25 секунд
На получение и запись 917 страниц уйдёт ~12109.27 секунд = ~201.82 минут = ~3.36 часа

1̶.̶ ̶У̶б̶р̶а̶т̶ь̶ ̶\\̶x̶a̶0̶ ̶в̶ ̶о̶п̶и̶с̶а̶н̶и̶я̶х̶
2̶.̶ ̶С̶д̶е̶л̶а̶т̶ь̶ ̶н̶о̶р̶м̶а̶л̶ь̶н̶у̶ю̶ ̶п̶а̶г̶и̶н̶а̶ц̶и̶ю̶ ̶с̶т̶р̶а̶н̶и̶ц̶
3̶.̶ ̶Д̶о̶б̶а̶в̶и̶т̶ь̶ ̶в̶и̶з̶у̶а̶л̶ь̶н̶ы̶е̶ ̶p̶r̶i̶n̶t̶-̶ы̶ ̶в̶ ̶к̶о̶н̶с̶о̶л̶ь̶ ̶(̶о̶т̶с̶л̶е̶ж̶и̶в̶а̶т̶ь̶ ̶х̶о̶д̶ ̶в̶ы̶п̶о̶л̶н̶е̶н̶и̶я̶ ̶п̶р̶о̶г̶р̶а̶м̶м̶ы̶)̶
4̶.̶ ̶С̶д̶е̶л̶а̶т̶ь̶ ̶о̶б̶р̶а̶б̶о̶т̶ч̶и̶к̶ ̶о̶ш̶и̶б̶о̶к̶ ̶(̶П̶о̶с̶л̶е̶ ̶1̶9̶5̶ ̶ф̶и̶л̶ь̶м̶а̶ ̶"̶Х̶а̶л̶о̶"̶ ̶в̶ы̶п̶а̶д̶а̶е̶т̶ ̶о̶ш̶и̶б̶к̶а̶!̶)̶
5̶.̶ ̶Р̶а̶з̶д̶е̶л̶и̶т̶ь̶ ̶к̶о̶д̶ ̶н̶а̶ ̶ф̶у̶н̶к̶ц̶и̶и̶
6̶.̶ ̶У̶с̶к̶о̶р̶и̶т̶ь̶ ̶п̶а̶р̶с̶и̶н̶г̶ ̶(̶а̶с̶и̶н̶х̶р̶о̶н̶н̶ы̶е̶ ̶ф̶у̶н̶к̶ц̶и̶)̶
7. Подключить прогресс бар
8. Засунуть в sql-базу
9. Привязать к телеграмм-боту
"""

user = fake_useragent.UserAgent().random

result_data = []
start_time = time.time()


async def get_page_data(client, page, pagination_count):
    """
    Получает список ссылок с фильмами со всех страниц и вносит в БД result_data
    :param session: Сохранённая сессия
    :param page: Номер страницы из пагинации
    :param pagination_count: Число страниц на сайте
    :return: Заполненный список result_data
    """
    header = {
        'User-Agent': user,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-en,ru;q=0.8,en-us;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'DNT': '1'
    }
    url = f'https://q.ixfilm.org/page/{page}/'

    async with client.get(url=url, headers=header) as response:
        bs = BeautifulSoup(await response.text(), 'html.parser')
        films_items = bs.find('div',
                              id='dle-content').find_all('a',
                                                         class_='th-in')

        list_urls = []

        for link in films_items:
            urls = link.get('href')
            list_urls.append(urls)

        # time.sleep(randrange(1, 3))
        print(f"[+] Page {page}/{pagination_count}")

        urls_count = len(list_urls)

        for url in enumerate(list_urls):
            # time.sleep(randrange(2, 5))
            try:
                response = await client.get(url=url[1], headers=header)
                bs = BeautifulSoup(await response.text(), 'html.parser')

                if response.status == 503:
                    continue
                else:
                    name_film = bs.find(
                        'div', class_='fleft-desc').find('h1').text.strip()
                    name_film = name_film[:-16]
                    poster = bs.find('div', class_='fleft').find(
                        'div', class_='img-wide').find('img').get('src')
                    descriprion = bs.find(
                        'div',
                        class_='fdesc').text.strip().replace(
                        '\n',
                        ' ').replace(
                        u'\xa0',
                        u' ')
                    year_of_release = bs.find(
                        'span', itemprop='dateCreated').text.strip()
                    director = bs.find(
                        'span', itemprop='director').text.strip()
                    actors = bs.find('span', itemprop='actors').text.strip()
                    rates_kp = bs.find('div', class_='frate-kp').text.strip()
                    rates_imdb = bs.find(
                        'div', class_='frate-imdb').text.strip()
                    print(f"[+] Page {page}/{pagination_count}")
                    result_data.append(
                        {
                            'poster': poster,
                            'name_film': name_film,
                            'description': descriprion,
                            'dateCreated': year_of_release,
                            'director': director,
                            'actors': actors,
                            'url': url[1],
                            'rates': {
                                'imdb': rates_imdb,
                                'kinopoisk': rates_kp
                            }
                        }
                    )
                # print(f'[+] Film {url[0] + 1}/{urls_count}')

                # async for i in tqdm(range(len(result_data))):
                #     if i == True:
                #         continue

            except BaseException as ex:
                print(f"Ошибка: {ex}")

            # finally:
        with open('result.json', 'w', encoding="utf-8") as file:
            json.dump(result_data, file, indent=4, ensure_ascii=False)


async def gather_data():
    """
    Открывает сессию, получает число страниц на сайте, создаёт список задач
    :return: Список задач
    """
    header = {
        'User-Agent': user,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'DNT': '1'
    }
    url = 'https://q.ixfilm.org/'
    connector = aiohttp.TCPConnector(limit=35)

    async with aiohttp.ClientSession(connector=connector, trust_env=True) as client:
        response = await client.get(url, headers=header)
        bs = BeautifulSoup(await response.text(), 'html.parser')
        pagination_count = int(
            bs.find('div', class_='navigation').find_all('a')[-1].text)

        tasks = []

        # for page in range(1, 3):
        for page in range(1, pagination_count + 1):
            task = asyncio.create_task(
                get_page_data(
                    client, page, pagination_count))
            tasks.append(task)
            await asyncio.sleep(1)

        await asyncio.gather(*tasks)


def main():
    asyncio.run(gather_data())
    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    asyncio.run(main())
