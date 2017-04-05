import multiprocessing
from functools import reduce
from bs4 import BeautifulSoup
import requests


def write_callback(data_arr):
    fangs = reduce(lambda arr, item: arr if item in arr else arr + [item], [[], ] + data_arr)
    with open('./output/anjuke.txt', 'a+') as f:
        f.writelines([line + "\r\n" for line in fangs])


def page_urls(city):
    web_city = requests.get(city)
    soup_city = BeautifulSoup(web_city.text, 'lxml')
    sum_city = int(soup_city.select('span.total > em:nth-of-type(1)')[0].get_text())
    page_num = sum_city / 50
    return [city + '/loupan/s?p={}'.format(str(i)) for i in range(1, int(page_num + 2), 1)]


def detail_page(city_tar):
    city_urls = page_urls(city_tar)
    fang = []
    for url in city_urls:
        web_city_data = requests.get(url)
        soup_city_data = BeautifulSoup(web_city_data.text, 'lxml')
        titles = soup_city_data.select('div.list-results > div.key-list > div > div.infos > div > h3 > a')
        for title in titles:
            fang.append(url + "\r" + title.get_text() + "\r" + title.get('href'))
            # print(url)
            # print(title.get_text())
            # print(title.get('href'))


def main(cities_arr):
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    for city in cities_arr:
        pool.apply_async(detail_page, (city, ), callback=write_callback)
    # pool.map(detailPage, urls)
    pool.close()
    pool.join()

if __name__ == "__main__":
    startUrl = 'http://sz.fang.anjuke.com/?from=navigation'
    web_data = requests.get(startUrl)
    soup = BeautifulSoup(web_data.text, 'lxml')
    cities = [url.get('href') for url in soup.select('.city-mod > dl > dd > a')]
    main(cities)

