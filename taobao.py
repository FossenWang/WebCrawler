from time import sleep
import os, re, traceback, random, requests

from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

from django import setup
from django.utils import timezone

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "storage.settings")
    setup()

from storage.models import TaobaoShop, TaobaoItem, TaobaoItemRecord


headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.4620.400 QQBrowser/9.7.13014.400'}


def rest(rest=(10, 20)):
    t = random.uniform(*rest)
    print('休息: %ds'%t)
    sleep(t)


class TaoBaoVisitor():
    '浏览淘宝网'
    def __init__(self):
        chrome_options = ChromeOptions()
        chrome_options.set_headless()
        self.driver = Chrome(chrome_options=chrome_options)
        self.driver.implicitly_wait(5)
        self.shops = None

    def quit(self):
        self.driver.quit()

    def get_shops(self):
        '获取收藏的店铺'
        if self.shops:
            return self.shops
        else:
            return TaobaoShop.objects.all()

    def get_all_items(self):
        '获取今日所有商品和价格'
        if not self.shops:
            self.shops = self.get_shops()
        for shop in self.shops:
            shop_url = shop.url
            if 'taobao' in shop_url:
                self.get_taobao_shop_items(shop)
            elif 'tmall' in shop_url:
                self.get_tmall_shop_items(shop)
            rest([180, 420])

    def get_taobao_shop_items(self, shop):
        '获取淘宝店铺中的商品及其价格'
        driver = self.driver
        driver.get(shop.get_list_url())
        shop_search_result = driver.find_elements_by_id('J_ShopSearchResult')[0]
        if shop.keyword:
            rest()
            input_keyword = shop_search_result.find_elements_by_name('keyword')[0]
            input_keyword.send_keys(shop.keyword)
            input_keyword.send_keys(Keys.RETURN)
        next_page = True
        while next_page:
            shop_search_result = driver.find_elements_by_id('J_ShopSearchResult')[0]
            items = shop_search_result.find_elements_by_css_selector('.item')
            self.collect_item_datas(items, shop)
            pagination_a = shop_search_result.find_elements_by_css_selector('.pagination-mini>a')
            next_page = False
            for a in pagination_a:
                if a.text=='下一页':
                    if not a.get_attribute('class'):
                        next_page =True
                        driver.execute_script('arguments[0].click();', a)
                        rest()

    def get_tmall_shop_items(self, shop):
        '获取天猫店铺中的商品及其价格'
        driver = self.driver
        driver.get(shop.get_list_url())
        rest()
        shop_search_result = driver.find_elements_by_id('J_ShopSearchResult')[0]
        if shop.keyword:
            input_keyword = shop_search_result.find_elements_by_name('keyword')[0]
            input_keyword.send_keys(shop.keyword)
            input_keyword.send_keys(Keys.RETURN)
            rest()
        next_page = True
        while next_page:
            shop_search_result = driver.find_elements_by_id('J_ShopSearchResult')[0]
            j_titems = shop_search_result.find_elements_by_css_selector('.J_TItems>div')
            items = []
            for div in j_titems:
                if div.get_attribute('class')=='pagination':
                    break
                else:
                    items += div.find_elements_by_css_selector('.item')
            self.collect_item_datas(items, shop)
            pagination_a = shop_search_result.find_elements_by_css_selector('.ui-page-s>a')
            next_page = False
            for a in pagination_a:
                if a.text=='>':
                    next_page = True
                    driver.execute_script('arguments[0].click();', a)
                    rest()
        
    def collect_item_datas(self, items, shop):
        '收集商品数据并保存至数据库'
        new_items = []
        new_records = []
        for item in items:
            item_id = item.get_attribute('data-id')
            if not TaobaoItem.objects.filter(id=item_id).exists():
                new_items.append(TaobaoItem(
                    id=item_id,
                    name=item.find_elements_by_css_selector('.detail>.item-name')[0].text,
                    shop_id=shop.id
                ))
                print(new_items[-1])
            today = timezone.now().date()
            if not TaobaoItemRecord.objects.filter(item_id=item_id, date=today).exists():
                new_records.append(TaobaoItemRecord(
                    item_id=item_id,
                    date=today,
                    price=float(item.find_elements_by_css_selector('.detail .c-price')[0].text)
                ))
                print(new_records[-1])
        TaobaoItem.objects.bulk_create(new_items)
        TaobaoItemRecord.objects.bulk_create(new_records)


def add_shop(url, keyword=None):
    '添加要追踪的店铺'
    url = url.split('com')[0] + 'com/'
    r = requests.get(url)
    match = re.search(r'shopId=([0-9]*)', r.text)
    if match:
        shop_id = int(match.group().replace('shopId=', ''))
        shop_name = re.search(r'<title>([.\n]*)</title>',r.text).group().split('-')[1]
        shop = TaobaoShop(id=shop_id, name=shop_name, url=url, keyword=keyword)
        shop.save()
        return shop
    else:
        print('无法找到该店铺')


def get_url_and_cookies(shop):
    chrome_options = ChromeOptions()
    chrome_options.set_headless()
    driver = Chrome(chrome_options=chrome_options)
    driver.get(shop.get_list_url())

    shop_asyn_search = driver.find_elements_by_id('J_ShopAsynSearchURL')[0]
    asyn_search_url = shop.url + shop_asyn_search.get_attribute('value') \
    + '&callback=jsonp' + str(random.randint(160,200))
    asyn_search_urls = [asyn_search_url]

    page_info = driver.find_elements_by_css_selector('.pagination-mini .page-info')[0].text
    for i in range(2, int(page_info.split('/')[1])+1):
        asyn_search_urls.append(asyn_search_url+'&pageNo='+str(i))

    full_cookies = driver.get_cookies()
    driver.quit()
    rest()
    return asyn_search_urls, {c['name']:c['value'] for c in full_cookies}


def asyn_search(shop):
    asyn_search_urls, cookies = get_url_and_cookies(shop)
    headers['referer'] = shop.get_list_url()
    for url in asyn_search_urls:
        print('爬取网站中：%s'%url)
        r = requests.get(url, headers=headers, cookies=cookies)
        soup = BeautifulSoup(r.text.replace('\\',''))
        items = soup.find_all(class_='item')
        for item in items:
            item_id = item['data-id']
            name = item.find(class_='item-name').text.replace(' ','')
            price = float(item.find(class_='c-price').text.replace(' ',''))
            print(item_id, name, price)
        rest()


if __name__ == "__main__":
    try:
        v = TaoBaoVisitor()
        v.get_all_items()
    except Exception as e:
        print(traceback.format_exc())
    v.quit()
