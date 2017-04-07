import multiprocessing
import codecs
import re
import asyncio
import time
from functools import reduce
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import lxml

# startUrl = 'http://sz.fang.anjuke.com/?from=navigation'
startUrl = "https://qs.888.qq.com/m_qq/mqq2.local.html"
phantom_path = "E:\Program_Coding\phantomjs\\bin\phantomjs"


def get_cookie():
    if not hasattr(get_cookie, 'cookie_arr'):
        get_cookie.cookie_arr = []
    if 0 >= len(get_cookie.cookie_arr):
        with codecs.open('./.cookie', 'r', 'utf-8') as file:
            cookies = file.read()
            cookies = cookies.split(';')
            for cookie in cookies:
                cookie_parts = cookie.split('=')
                if cookie_parts and cookie_parts[0] and cookie_parts[1]:
                    get_cookie.cookie_arr.append({"name": cookie_parts[0], "value": cookie_parts[1], "domain": ".qq.com", 'path': '/', 'expires': None})
    return get_cookie.cookie_arr


# def write_callback(data_arr):
#     fangs = reduce(lambda arr, item: arr if item in arr else arr + [item], [[], ] + data_arr)
#     with codecs.open('./output/anjuke.txt', 'a+', "utf-8") as f:
#         f.writelines([line + "\r\n" for line in fangs])


def write_callback(data_arr):
    fangs = reduce(lambda arr, item: arr if item in arr else arr + [item], [[], ] + data_arr)
    with codecs.open('./output/888.txt', 'a+', "utf-8") as f:
        f.writelines([line + "\r\n" for line in fangs])


def page_urls(driver, url):
    driver.delete_all_cookies()
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    url_pre = driver.execute_script('return window.location.protocol + "//" + window.location.host')

    pages = []
    for url in soup.select('[url]'):
        url_tmp = url.get('url')
        if re.match(r'http(s)?://', url_tmp):
            pages.append(url_tmp)
        else:
            pages.append(url_pre + url_tmp)
    images = []
    for img in soup.select('img'):
        img_tmp = img.get('src')
        if re.match(r'http(s)?://', img_tmp):
            images.append(img_tmp)
        else:
            images.append(url_pre + img_tmp)

    return {"pages": pages, "images": images}
    # page_num = sum_city / 50
    # return [url + '/loupan/s?p={}'.format(str(i)) for i in range(1, int(page_num + 2), 1)]


def detail_page(url, cookies):
    driver = webdriver.PhantomJS(phantom_path)
    driver.delete_all_cookies()
    for cookie in cookies:
        driver.add_cookie(cookie)
    urls = page_urls(driver, url)
    print(url, urls)
    return [url].extend([url_tmp for url_tmp in urls['pages']]).extend([img_tmp for img_tmp in urls['images']])
    # fang = []
    # for url in urls:
    #     driver.get(url)
    #     soup = BeautifulSoup(driver.page_source, 'lxml')
    #     titles = soup.select('div.list-results > div.key-list > div > div.infos > div > h3 > a')
    #     for title in titles:
    #         print(title.get_text())
    #         fang.append(url + "\t" + title.get_text() + "\t" + title.get('href'))
    #         # print(url)
    #         # print(title.get_text())
    #         # print(title.get('href'))
    # return fang


def main(cities_arr):
    pool = multiprocessing.Pool(multiprocessing.cpu_count() * 3)
    for city in cities_arr:
        pool.apply_async(detail_page, (city, get_cookie()), callback=write_callback)
    # pool.map(detailPage, urls)
    pool.close()
    pool.join()



# if __name__ == "__main__":
#     driver = webdriver.PhantomJS(phantom_path)
#     driver.delete_all_cookies()
#     for cookie in phantom_cookie:
#         driver.add_cookie(cookie)
#     driver.get(startUrl)
#
#     container = re.search(r"[\"']containerId[\"']:\s*[\"'](.*?)[\"']", driver.page_source)
#     if container:
#         element_xpath = '//*[@id="' + container.group(1) + '"]/div/*'
#     else:
#         element_xpath = '//body/div/*'
#     time_out = 10
#     wait = WebDriverWait(driver, time_out).until(
#         expected_conditions.presence_of_element_located((By.XPATH, element_xpath))
#     )
#     if wait:
#         soup = BeautifulSoup(driver.page_source, 'lxml')
#         url_pre = driver.execute_script('return window.location.protocol + "//" + window.location.host')
#         pages = []
#         for url in soup.select('[url]'):
#             url_tmp = url.get('url')
#             if re.match(r'http(s)?://', url_tmp):
#                 pages.append(url.get('url'))
#             else:
#                 pages.append(url_pre + url.get('url'))
#         print(pages)
#         main(pages)
#


async def wait_element(driver, xpath, time_limit=10, time_step=.25):
    end_time = time.time() + time_limit
    while True:
        value = driver.find_elements(By.XPATH, xpath)
        if value:
            return True
        asyncio.sleep(time_step)
        if time.time() > end_time:
            break
    return False


async def get_url_888(driver, url, cookies):
    driver.delete_all_cookies()
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get(url)

    container = re.search(r"[\"']containerId[\"']:\s*[\"'](.*?)[\"']", driver.page_source)
    if container:
        element_xpath = '//*[@id="' + container.group(1) + '"]/div/*'
    else:
        element_xpath = '//body/div/*'

    elements = await wait_element(driver, element_xpath)

    if elements:
        soup = BeautifulSoup(driver.page_source, 'lxml')
        url_pre = driver.execute_script('return window.location.protocol + "//" + window.location.host')
        pages = []
        for url in soup.select('[url]'):
            url_tmp = url.get('url')
            if re.match(r'http(s)?://', url_tmp):
                pages.append(url.get('url'))
            else:
                pages.append(url_pre + url.get('url'))
        print(pages)
        # main(pages)
    else:
        print('program cannot load pages, are you logged in?')

if __name__ == "__main__":
    driver = webdriver.PhantomJS(phantom_path)
    # get_url_888(driver, startUrl)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_url_888(driver, startUrl, get_cookie()))
    loop.close()


    # wait = WebDriverWait(driver, time_out).until(
    #     expected_conditions.presence_of_element_located((By.XPATH, element_xpath))
    # )
    # if wait:
    #     soup = BeautifulSoup(driver.page_source, 'lxml')
    #     url_pre = driver.execute_script('return window.location.protocol + "//" + window.location.host')
    #     pages = []
    #     for url in soup.select('[url]'):
    #         url_tmp = url.get('url')
    #         if re.match(r'http(s)?://', url_tmp):
    #             pages.append(url.get('url'))
    #         else:
    #             pages.append(url_pre + url.get('url'))
    #     print(pages)
    #     main(pages)
