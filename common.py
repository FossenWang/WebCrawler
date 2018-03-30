import os, sys, random
from time import sleep

from django import setup
from django.core.mail import send_mail


def rest(rest=(1, 5)):
    t = random.uniform(*rest)
    print('休息: %ds'%t)
    sleep(t)


def setup_django():
    os.chdir('/usr/fossen/website/WebCrawler')
    sys.path.append(os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "storage.settings")
    setup()


def send_email(title, message, html=None):
    send_mail(
        title,
        message,
        'admin@fossen.cn',
        ['fossen@fossen.cn'],
        html_message=html
    )#在setting.py中定义邮箱与密码
