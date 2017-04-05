import multiprocessing
import codecs
import re
from functools import reduce
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import lxml

# startUrl = 'http://sz.fang.anjuke.com/?from=navigation'
startUrl = "https://qs.888.qq.com/m_qq/mqq2.local.html"
phantom_path = "D:\Program_Coding\phantomjs\\bin\phantomjs"
phantom_cookie = [{"name": "uin", "value": "o0862683427", "domain": ".qq.com", 'path': '/', 'expires': None}, {"name": "skey", "value": "@ZlEUiQzvY", "domain": ".qq.com", 'path': '/', 'expires': None}]


def write_callback(data_arr):
    fangs = reduce(lambda arr, item: arr if item in arr else arr + [item], [[], ] + data_arr)
    with codecs.open('./output/anjuke.txt', 'a+', "utf-8") as f:
        f.writelines([line + "\r\n" for line in fangs])


def page_urls(url):
    driver = webdriver.PhantomJS(phantom_path)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    sum_city = int(soup.select('span.total > em:nth-of-type(1)')[0].get_text())
    page_num = sum_city / 50
    return [url + '/loupan/s?p={}'.format(str(i)) for i in range(1, int(page_num + 2), 1)]


def detail_page(url):
    urls = page_urls(url)
    print(urls)
    fang = []
    driver = webdriver.PhantomJS(phantom_path)
    for url in urls:
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        titles = soup.select('div.list-results > div.key-list > div > div.infos > div > h3 > a')
        for title in titles:
            print(title.get_text())
            fang.append(url + "\t" + title.get_text() + "\t" + title.get('href'))
            # print(url)
            # print(title.get_text())
            # print(title.get('href'))
    return fang


def main(cities_arr):
    pool = multiprocessing.Pool(multiprocessing.cpu_count() * 3)
    for city in cities_arr:
        pool.apply_async(detail_page, (city, ), callback=write_callback)
    # pool.map(detailPage, urls)
    pool.close()
    pool.join()

if __name__ == "__main__":
    driver = webdriver.PhantomJS(phantom_path)
    driver.delete_all_cookies()
    for cookie in phantom_cookie:
        driver.add_cookie(cookie)
    driver.get(startUrl)

    container = re.search(r"[\"']containerId[\"']:\s*[\"'](.*?)[\"']", driver.page_source)
    if container:
        element_xpath = '//*[@id="' + container.group(1) + '"]/div/*'
    else:
        element_xpath = '//body/div/*'
    time_out = 10
    wait = WebDriverWait(driver, time_out).until(
        expected_conditions.presence_of_element_located((By.XPATH, element_xpath))
    )
    if wait:
        print(driver.page_source)

    # soup = BeautifulSoup(driver.page_source, 'lxml')
    # cities = [url.get('href') for url in soup.select('.city-mod > dl > dd > a')]
    # main(cities)

