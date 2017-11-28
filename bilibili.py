'''
B站爬虫
'''
from io import BytesIO
from datetime import datetime
import requests
from django.utils import timezone
from PIL import Image

#这里导入的是我另外开发的一个的django网站中的模型，用于保存数据至数据库，有时导入Video类的路径可能会与下面不同
from DjangoBlog.video.models import Video

SUBMITVIDEOS = 'http://space.bilibili.com/ajax/member/getSubmitVideos'

def get_submit_videos(mid, pagesize=200, tid=0, page=1, keyword='', order='pubdate'):
    '根据哔哩哔哩的api获取视频信息'
    r = requests.get(SUBMITVIDEOS,params={
        'mid':mid,
        'pagesize':pagesize,
        'tid':tid, 'page':page,
        'keyword':keyword,
        'order':order})
    #api示例：http://space.bilibili.com/ajax/member/getSubmitVideos?mid=95083523&pagesize=200&tid=0&page=1&keyword=&order=pubdate
    json = r.json()    #返回字典
    count = json['data']['count']    #总视频数
    pages = json['data']['pages']    #总页数
    vlist = json['data']['vlist']    #视频列表
    vlist.reverse()
    i = 0
    for video in vlist:
        video_url = 'http://static.hdslb.com/miniloader.swf?aid='+str(video['aid'])+'&page=1'
        pub_date = datetime.fromtimestamp(video['created'], tz=timezone.utc)
        description = video['description']
        length = video['length']
        title = video['title']
        pic = requests.get('http://'+video['pic'][2:])
        try:
            img = Image.open(BytesIO(pic.content))
            img.save('F:/Project/Python/DjangoBlog/media/video/cover/'+video['pic'].split('/')[-1],'jpeg')
            cover ='video/cover/'+video['pic'].split('/')[-1]
        except OSError as e:
            cover ='public/images/nonpic.jpg'
            print('无法获取该视频的图片：aid='+str(video['aid']))
        video_model = Video(title=title, video=video_url, video_length=length, cover=cover, note=description, pub_date=pub_date)
        video_model.save()
        i+=1
        print('第'+str(i)+'个视频已保存  aid='+str(video['aid']))
