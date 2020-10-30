# coding:utf-8
import json
import requests
import pymongo
from sshtunnel import SSHTunnelForwarder

host = "49.233.52.61"
port = 22
# better changed to SSH
username = "ubuntu"
password = "48*~VbNY93Aq"
database_name = "StaticNews"
db_port = 27017
local_port = 27018 # should be different from `db_port`
colomn_name = "news"
http_prefix = "http:"
lucene_url = "https://wooohooo-indexquery-wooohooo.app.secoder.net/queryNews"

type_map = {
    "热点": "news",
    "国内": "politics",
    "文化": "history",  # "cul"
    "社会": "social",
    "国际": "chuguo",
    "军事": "mil",
    "财经": "finance",
    "娱乐": "ent",
    "体育": "sports", 
    "科技": "science", # "tech"
    "游戏": "game",
}

def decode(news):
    if news["top_img"] and len(news["top_img"]) > 5:
        img_url = http_prefix + news["top_img"]
    else:
        imgs = json.loads(news["imageurl"])
        if len(imgs) > 0:
            img_url = http_prefix + imgs[0]
        else:
            img_url = ""
    return {
        "uid": str(news['_id']),
        "link": news["url"],
        "title": news["title"],
        "content": news["content"][:300],
        "imgurl": img_url,
        "source": news["source"],
        "time": news["publish_time"]
    }

def fetch_typed_news(news_type, number, page):
    total = 0
    result = []
    with SSHTunnelForwarder(
        ssh_address_or_host=(host, port),  # 远程主机ip, port
        ssh_username=username,  # ssh用户名密码
        ssh_password=password,
        remote_bind_address=('127.0.0.1', db_port),     # 远程服务ip, port
        local_bind_address=('localhost', local_port)    # 转发到本地服务ip, port
    ) as server:
        newsdb_client = pymongo.MongoClient(f"mongodb://localhost:{local_port}/")
        newsdb = newsdb_client[database_name]
        news_col = newsdb[type_map[news_type]]
        print(news_col)
        query = {}
        ret_field = { # 为1的字段会返回
            '_id': 1,
            "title": 1,
            "publish_time": 1,
            "source": 1,
            "imageurl": 1,
            "url": 1,
            'content': 1,
            "top_img": 1,
        }
        total = news_col.count()
        for x in news_col.find(query, ret_field).skip(page*number).limit(number):  # 注意限制个数，不然数据量可能极大
            result.append(decode(x))
        newsdb_client.close()
        print("**** exit from server ****")
    return total, result


def fetch_search_result(query, number, page):
    total = 1000
    result = []
    #向java端发送检索请求
    try:
        params = {
            "name": query,
            "page": page,
            "number": number
        }
        response = requests.get(url=lucene_url, params=params)
        newslist = json.loads(response.text)
        for x in newslist:
            result.append(decode(x))
    except Exception as e:
        print("error:", e)
    return total, result