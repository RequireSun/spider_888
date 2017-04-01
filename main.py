import unittest
import os
import codecs
from selenium import webdriver
from bs4 import BeautifulSoup
import lxml


class SeleniumTest(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.PhantomJS("E:\Program_Coding\phantomjs\\bin\phantomjs")

    def testEle(self):
        if not os.path.exists('./output'):
            os.makedirs('./output')
        self.rooms = codecs.open("./output/douyu.txt", "w", "utf-8")
        page = 0
        driver = self.driver
        driver.get('http://www.douyu.com/directory/all')
        soup = BeautifulSoup(driver.page_source, 'xml')
        while True:
            page += 1
            print('parsing page:', page)
            titles = soup.find_all('h3', {'class': 'ellipsis'})
            nums = soup.find_all('span', {'class': 'dy-num fr'})
            rooms = []
            for title, num in zip(titles, nums):
                rooms.append(title.get_text().strip() + "\t" + num.get_text().strip())
            self.rooms.writelines([line + "\r\n" for line in rooms])
            if driver.page_source.find('shark-pager-disable-next') != -1:
                break
            elem = driver.find_element_by_class_name('shark-pager-next')
            elem.click()
            soup = BeautifulSoup(driver.page_source, 'xml')

    def tearDown(self):
        # for item in self.rooms:
            # print(item['title'], item['text'])
        self.rooms.close()
        print('down')

if __name__ == "__main__":
    unittest.main()

