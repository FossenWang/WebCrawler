'薛之谦的淘宝店'
import time, requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

shop_list_url='https://xuezhiqiandsp.taobao.com/i/asynSearch.htm?callback=jsonp205&mid=w-15378812034-0'
pageNo = '&pageNo='
headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.4620.400 QQBrowser/9.7.13014.400'}
TIMEOUT = 3

def getCookies():
    chrome_options = Options()
    chrome_options.set_headless()
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get('https://www.taobao.com')
    full_cookies = driver.get_cookies()
    driver.close()
    time.sleep(TIMEOUT)
    return {c['name']:c['value'] for c in full_cookies}


def main():
    cookies=getCookies()
    r = requests.get(shop_list_url, headers=headers, cookies=cookies)
    r.text[:500]

if __name__ == "__main__":
    main()