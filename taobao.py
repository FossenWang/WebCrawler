from time import sleep
from random import uniform
import requests, re

from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.keys import Keys

from django.utils import timezone
from storage.models import TaobaoShop, TaobaoItem, TaobaoItemRecord

# driver.execute_script('window.open()')
# driver.window_handles
TIMEOUT = (3, 6)

def rest(rest=TIMEOUT):
    sleep(uniform(*rest))

class TaoBaoVisitor():
    '浏览淘宝网'
    def __init__(self):
        chrome_options = ChromeOptions()
        #chrome_options.set_headless()
        self.driver = Chrome(chrome_options=chrome_options)
        self.driver.implicitly_wait(5)
        self.shops = None

    def quit(self):
        self.driver.quit()

    def get_shops(self):
        if self.shops:
            return self.shops
        else:
            return TaobaoShop.objects.all()

    def get_all_items(self):
        if not self.shops:
            self.shops = self.get_shops()
        for shop in self.shops:
            shop_items_url = shop.get_list_url()
            if 'taobao' in shop_items_url:
                self.get_taobao_shop_items(shop)
            elif 'tmall' in shop_items_url:
                self.get_tmall_shop_items(shop)

    def get_taobao_shop_items(self, shop):
        driver = self.driver
        driver.get(shop.get_list_url())
        shop_search_result = driver.find_elements_by_id('J_ShopSearchResult')[0]
        if shop.keyword:
            input_keyword = shop_search_result.find_elements_by_name('keyword')[0]
            input_keyword.send_keys(shop.keyword)
            input_keyword.send_keys(Keys.RETURN)
        next_page = True
        while next_page:
            shop_search_result = driver.find_elements_by_id('J_ShopSearchResult')[0]
            items = shop_search_result.find_elements_by_css_selector('.item')
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
                today = timezone.now().date()
                if not TaobaoItemRecord.objects.filter(
                    item_id=item_id,
                    date=today,
                    ).exists():
                    new_records.append(TaobaoItemRecord(
                        item_id=item_id,
                        date=today,
                        price=float(item.find_elements_by_css_selector('.detail .c-price')[0].text)
                    ))
            TaobaoItem.objects.bulk_create(new_items)
            TaobaoItemRecord.objects.bulk_create(new_records)
            print(new_items)
            print(new_records)
            pagination_a = shop_search_result.find_elements_by_css_selector('.pagination-mini>a')
            for a in pagination_a:
                if a.text=='下一页':
                    if not a.get_attribute('class'):
                        rest()
                        a.click()
                    else:
                        next_page = False

    def get_tmall_shop_items(self, shop):
        driver = self.driver
        driver.get(shop.get_list_url())
        shop_search_result = driver.find_elements_by_id('J_ShopSearchResult')[0]
        if shop.keyword:
            input_keyword = shop_search_result.find_elements_by_name('keyword')[0]
            input_keyword.send_keys(shop.keyword)
            input_keyword.send_keys(Keys.RETURN)
        next_page = True
        while next_page:
            shop_search_result = driver.find_elements_by_id('J_ShopSearchResult')[0]
            j_titems = shop_search_result.find_elements_by_css_selector('.J_TItems>div')
            items = []
            new_items = []
            new_records = []
            for div in j_titems:
                if div.get_attribute('class')=='pagination':
                    break
                else:
                    items+=div.find_elements_by_css_selector('.item')
            for item in items:
                item_id = item.get_attribute('data-id')
                if not TaobaoItem.objects.filter(id=item_id).exists():
                    new_items.append(TaobaoItem(
                        id=item_id,
                        name=item.find_elements_by_css_selector('.detail>.item-name')[0].text,
                        shop_id=shop.id
                    ))
                today = timezone.now().date()
                if not TaobaoItemRecord.objects.filter(
                    item_id=item_id,
                    date=today,
                    ).exists():
                    new_records.append(TaobaoItemRecord(
                        item_id=item_id,
                        date=today,
                        price=float(item.find_elements_by_css_selector('.detail .c-price')[0].text)
                    ))
            TaobaoItem.objects.bulk_create(new_items)
            TaobaoItemRecord.objects.bulk_create(new_records)
            print(new_items)
            print(new_records)
            pagination_a = shop_search_result.find_elements_by_css_selector('.ui-page-s>a')
            next_page = False
            for a in pagination_a:
                if a.text=='>':
                    next_page = True
                    rest()
                    a.click()


def add_shop(url, keyword):
    url = url.split('com')[0] + 'com/'
    r = requests.get(url)
    match = re.search(r'shopId=([0-9]*)', r.text)
    if match:
        shop_id = int(match.group().replace('shopId=', ''))
        shop_name = re.search(r'<title>((.|\n)*)</title>',r.text).group().split('-')[1]
        shop = TaobaoShop(id=shop_id, name=shop_name, url=url, keyword=keyword)
        shop.save()
        return shop
    else:
        print('无法找到该店铺')


if __name__ == "__main__":
    v = TaoBaoVisitor()
    v.get_all_items()
    v.quit()
