'爬虫数据模型'
from django.db import models


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
        return self.url+'search.htm'


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
