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
url_pool = [{"url": "https://qs.888.qq.com/m_qq/mqq2.local.html", "depth": 1}]
visited_pool = []
max_depth = 7
multiple = 3


def search_pool(key):
    """在未遍历 pool 中进行遍历
    Args:
        key: 地址
    Returns:
        True: key 不存在 / key 不合理 / key 已存在
        False: key 不存在 (可以插入)
    """
    global url_pool
    if not key:
        return True
    if not len(url_pool):
        return False
    key = re.match(r'(http(?:s)?://[^\?#]*)[^#]*(#[^&]*)?', key)
    if key:
        for url in url_pool:
            url = url["url"]
            if 0 > url.find(key.group(1)) and (not key.group(2) or 0 > url.find(key.group(2))):
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
    global visited_pool
    if not key:
        return True
    if not len(visited_pool):
        return False
    key = re.match(r'(http(?:s)?://[^\?#]*)[^#]*(#[^&]*)?', key)
    if key:
        for url in visited_pool:
            url = url["url"]
            if 0 > url.find(key.group(1)) and (not key.group(2) or 0 > url.find(key.group(2))):
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
    global url_pool
    urls = reduce(lambda arr, item: arr if item in arr else arr + [item], [[], ] + data_arr)
    url_pool = url_pool + data_arr
    with codecs.open('./output/888.txt', 'a+', "utf-8") as f:
        f.writelines([line["url"] + "\r\n" for line in urls])


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

    # driver = webdriver.PhantomJS(phantom_path)
    # driver.delete_all_cookies()
    # for cookie in cookies:
    #     driver.add_cookie(cookie)
    # urls = page_urls(driver, url)
    # print(url, urls)
    # return [url].extend([url_tmp for url_tmp in urls['pages']]).extend([img_tmp for img_tmp in urls['images']])


async def wait_element(driver, xpath, not_empty_xpath, time_limit=10, time_step=.25):
    end_time = time.time() + time_limit
    while True:
        value = driver.find_elements(By.XPATH, xpath)
        # 就算页面加载上了, 也还是会有延迟加载的东西, 导致元素丢失, 绝望了, 改成强制 8 秒了
        # value = end_time - time.time() < 2

        if value:
            value = driver.find_elements(By.XPATH, not_empty_xpath)
            mark = True
            for it in value:
                if not len(it.find_elements_by_xpath('*')):
                    mark = False
            if mark:
                return True
        await asyncio.sleep(time_step)
        if time.time() > end_time:
            break
    return False


def should_push_to_arr(url, url_pre, depth):
    global url_pool
    global max_depth
    if not re.match(r'http(s)?://', url):
        url = url_pre + url
    # print(url, search_pool(url), search_visited(url))
    if not search_pool(url) and not search_visited(url) and depth + 1 < max_depth:
        # url_pool.append({"url": url, "depth": depth + 1})
        return url
    else:
        return None


async def async_page(url, depth):
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
    not_empty_xpath = '//ul'

    element = await wait_element(driver, element_xpath, not_empty_xpath)

    if element:
        res = []
        print('processing:', url)
        # print(driver.page_source)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        url_pre = driver.execute_script('return window.location.protocol + "//" + window.location.host')

        # 因为单独的属性选择器会有 bug, 导致只能选到一条, 所以前面加了个父元素
        for elem_url in soup.select('div [url]'):
            pushed = should_push_to_arr(elem_url.get('url'), url_pre, depth)
            # print('got', pushed, elem_url)
            if pushed:
                res.append({"url": pushed, "depth": depth + 1})
        for elem_url in soup.select('a[href]'):
            pushed = should_push_to_arr(elem_url.get('href'), url_pre, depth)
            # print('got', pushed, elem_url)
            if pushed:
                res.append({"url": pushed, "depth": depth + 1})
        return res
    else:
        print('program cannot load pages, are you logged in?')
        return None


def detail_page(url, depth):
    print("dealing url:", url)
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(async_page(url, depth))
    loop.close()
    return res

if __name__ == "__main__":
    while len(url_pool):
        pool = multiprocessing.Pool(multiprocessing.cpu_count() * multiple)
        for url in url_pool:
            pool.apply_async(detail_page, (url["url"], url["depth"]), callback=write_callback)
        move_to_visited()
        pool.close()
        pool.join()
    print(url_pool)
    print(visited_pool)
