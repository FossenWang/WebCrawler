from datetime import datetime
import requests, traceback

from bs4 import BeautifulSoup
from django.utils import timezone
from common import setup_django, send_email, rest

if __name__ == "__main__":
    setup_django()

from storage.models import ZhihuPeople, ZhihuArticle, ZhihuQuestion, ZhihuAnswer


headers = {
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.4620.400 QQBrowser/9.7.13014.400',
    'authorization':'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'
    }


class ZhihuVisitor():
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = headers
        self.people = None

    def get_people(self):
        if not self.people:
            self.people = ZhihuPeople.objects.all()
        return self.people

    def get_people_posts(self):
        people = self.get_people()
        for author in people:
            self.get_posts(author)

    def get_posts(self, author):
        s = self.session
        # 检查是否更新
        post_url = author.get_posts_url()
        r = s.get(post_url)
        soup = BeautifulSoup(r.text, "html.parser")
        time_str = soup.find(itemprop="datePublished")['content']
        try:
            newest_created = timezone.make_aware(datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%fZ'))
            first = author.zhihuarticle_set.all()[0]
            if newest_created <= first.created:
                print('文章暂未更新')
                return
        except IndexError:
            pass
        # 读取文章信息
        s.headers['referer'] = post_url
        offset = 0
        api = author.get_articles_api()
        next_page = api.format(offset)
        is_end = False
        new_articles = []
        rest()
        while not is_end:
            r = s.get(next_page)
            j = r.json()
            is_end = j['paging']['is_end']
            for data in j['data']:
                created = timezone.make_aware(datetime.fromtimestamp(int(data['created'])))
                if not ZhihuArticle.objects.filter(id=data['id']).exists():
                    new_articles.append(ZhihuArticle(
                        id=data['id'],
                        title=data['title'],
                        content=data['content'],
                        created=created,
                        author=author
                    ))
                    print(new_articles[-1])
                else:
                    is_end = True
                    break
            offset += 20
            next_page = api.format(offset)
            rest()
        ZhihuArticle.objects.bulk_create(new_articles)
        print('已保存{}篇文章'.format(len(new_articles)))

    def get_people_answers(self):
        people = self.get_people()
        for author in people:
            self.get_answers(author)

    def get_answers(self, author):
        s = self.session
        # 检查是否更新
        answers_url = author.get_answers_url()
        r = s.get(answers_url)
        soup = BeautifulSoup(r.text, "html.parser")
        time_str = soup.find(itemprop="dateCreated")['content']
        try:
            newest_created = timezone.make_aware(datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%fZ'))
            first = author.zhihuanswer_set.all()[0]
            if newest_created <= first.created:
                print('回答暂未更新')
                return
        except IndexError:
            pass
        # 读取文章信息
        s.headers['referer'] = answers_url
        offset = 0
        api = author.get_answers_api()
        next_page = api.format(offset)
        is_end = False
        new_answers = []
        new_question = []
        rest()
        while not is_end:
            r = s.get(next_page)
            j = r.json()
            is_end = j['paging']['is_end']
            for data in j['data']:
                q = data['question']
                question_id = q['id']
                if not ZhihuQuestion.objects.filter(id=q['id']).exists():
                    new_question.append(ZhihuQuestion(
                        id=question_id,
                        title=q['title'],
                        created=timezone.make_aware(datetime.fromtimestamp(int(q['created'])))
                    ))
                    print(new_question[-1])
                created = timezone.make_aware(datetime.fromtimestamp(int(data['created_time'])))
                if not ZhihuAnswer.objects.filter(id=data['id']).exists():
                    new_answers.append(ZhihuAnswer(
                        id=data['id'],
                        content=data['content'],
                        created=created,
                        author=author,
                        question_id=question_id
                    ))
                    print(new_answers[-1])
                else:
                    is_end = True
                    break
            offset += 20
            next_page = api.format(offset)
            rest()
        ZhihuQuestion.objects.bulk_create(new_question)
        ZhihuAnswer.objects.bulk_create(new_answers)
        print('已保存{}个问题和{}个回答'.format(len(new_question), len(new_answers)))


def add_people(url):
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    name = soup.find(class_='ProfileHeader-name').text
    if name:
        p, created = ZhihuPeople.objects.get_or_create(name=name, url_token=url.split('/')[4])
        if created:
            p.save()
        return p
    else:
        print('找不到该知乎用户: '+url)


if __name__ == "__main__":
    try:
        v = ZhihuVisitor()
        v.get_people_posts()
        v.get_people_answers()
    except Exception:
        send_email('知乎爬虫运行出错!', traceback.format_exc())
