import multiprocessing
import codecs
import re
import asyncio
import time
from functools import reduce
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

# startUrl = "https://qs.888.qq.com/m_qq/mqq2.local.html"
phantom_path = "E:\Program_Coding\phantomjs\\bin\phantomjs"
url_pool = ["https://qs.888.qq.com/m_qq/mqq2.local.html"]
visited_pool = []


def search_pool(key):
    """在未遍历 pool 中进行遍历
    Args:
        key: 地址
    Returns:
        True: key 不存在 / key 不合理 / key 已存在
        False: key 不存在 (可以插入)
    """
    if not key:
        return True
    key = re.match(r'(http(?:s)?://[^\?#]*)[^#]*(#[^&]*)?', key)
    if key:
        for url in url_pool:
            if -1 < url.find(key.group(1)) and (not key.group(2) or -1 < url.find(key.group(2))):
                return False
            else:
                return True
    else:
        return True


def search_visited(key):
    """在未遍历 pool 中进行遍历
    Args:
        key: 地址
    Returns:
        True: key 不存在 / key 不合理 / key 已存在
        False: key 不存在 (可以插入)
    """
    if not key:
        return True
    key = re.match(r'(http(?:s)?://[^\?#]*)[^#]*(#[^&]*)?', key)
    if key:
        for url in visited_pool:
            if -1 < url.find(key.group(1)) and (not key.group(2) or -1 < url.find(key.group(2))):
                return False
            else:
                return True
    else:
        return True


def move_to_visited():
    global url_pool
    global visited_pool
    visited_pool = visited_pool + url_pool
    url_pool = []


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


async def detail_page(url):
    driver = webdriver.PhantomJS(phantom_path)
    cookies = get_cookie()
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
        global url_pool
        soup = BeautifulSoup(driver.page_source, 'lxml')
        url_pre = driver.execute_script('return window.location.protocol + "//" + window.location.host')
        for url in soup.select('[url]'):
            url_tmp = url.get('url')
            if not re.match(r'http(s)?://', url_tmp):
                url_tmp = url_pre + url_tmp
            if not search_pool(url_tmp) and not search_visited(url_tmp):
                url_pool.append({"url": url_tmp})
    else:
        print('program cannot load pages, are you logged in?')

    # driver = webdriver.PhantomJS(phantom_path)
    # driver.delete_all_cookies()
    # for cookie in cookies:
    #     driver.add_cookie(cookie)
    # urls = page_urls(driver, url)
    # print(url, urls)
    # return [url].extend([url_tmp for url_tmp in urls['pages']]).extend([img_tmp for img_tmp in urls['images']])


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


async def process_controller():
    pool = multiprocessing.Pool(multiprocessing.cpu_count() * 3)
    for url in url_pool:
        pool.apply_async(detail_page, (url, ), callback=write_callback)
    move_to_visited()
    pool.close()
    pool.join()


if __name__ == "__main__":
    while len(url_pool):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(process_controller())
        loop.close()
