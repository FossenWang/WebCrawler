'爬虫数据模型'
from django.db import models


class ZhihuPeople(models.Model):
    '知乎用户'
    name = models.CharField('名称', max_length=50)
    url_token = models.CharField( max_length=50)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return 'https://www.zhihu.com/people/{}/activities'.format(self.url_token)
    
    def get_posts_url(self):
        return 'https://www.zhihu.com/people/{}/posts'.format(self.url_token)
    
    def get_articles_api(self):
        return ('https://www.zhihu.com/api/v4/members/'+ self.url_token
        + '/articles?include=data[*].content,created&offset={}&limit=20&sort_by=created')

    def get_answers_url(self):
        return 'https://www.zhihu.com/people/{}/answers'.format(self.url_token)

    def get_answers_api(self):
        return ('https://www.zhihu.com/api/v4/members/'+ self.url_token
        + '/answers?include=data[*].content,created_time,question&offset={}&limit=20&sort_by=created')

class ZhihuArticle(models.Model):
    id = models.BigIntegerField(primary_key=True)
    title = models.CharField('标题', max_length=100)
    content = models.TextField('内容')
    created = models.DateTimeField('发布日期')
    author = models.ForeignKey(ZhihuPeople, on_delete=models.CASCADE, verbose_name='作者')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return 'https://zhuanlan.zhihu.com/p/{}'.format(self.id)

    class Meta:
        ordering = ['-created']

class ZhihuQuestion(models.Model):
    id = models.BigIntegerField(primary_key=True)
    title = models.CharField('标题', max_length=100)
    created = models.DateTimeField('发布日期')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return 'https://www.zhihu.com/question/{}'.format(self.id)

    class Meta:
        ordering = ['-created']

class ZhihuAnswer(models.Model):
    id = models.BigIntegerField(primary_key=True)
    content = models.TextField('内容')
    created = models.DateTimeField('发布日期')
    author = models.ForeignKey(ZhihuPeople, on_delete=models.CASCADE, verbose_name='作者')
    question = models.ForeignKey(ZhihuQuestion, on_delete=models.CASCADE, verbose_name='问题')

    def __str__(self):
        return self.content[:50]

    def get_absolute_url(self):
        return 'https://www.zhihu.com/question/{}/answer/{}'.format(self.question.id, self.id)

    class Meta:
        ordering = ['-created']


class TaobaoShop(models.Model):
    '淘宝店铺'
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField('名称', max_length=50)
    url = models.URLField('网址')
    keyword = models.CharField('搜索词', blank=True, null=True, max_length=50)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return self.url

    def get_list_url(self):
        if 'taobao' in self.url:
            return self.url + 'search.htm'
        elif 'tmall' in self.url:
            return self.url + 'category.htm'


class TaobaoItem(models.Model):
    '淘宝商品'
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField('名称', max_length=100)
    shop = models.ForeignKey(TaobaoShop, related_name='items', on_delete=models.CASCADE, verbose_name='店铺')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return 'https://item.taobao.com/item.htm?id=' + str(self.id)


class TaobaoItemRecord(models.Model):
    '淘宝商品记录'
    item = models.ForeignKey(TaobaoItem, related_name='records', on_delete=models.CASCADE, verbose_name='商品')
    price = models.FloatField('价格')
    date = models.DateField(auto_now=True)
    
    def __str__(self):
        return str(self.date) + ': ' + str(self.price)
