#! /usr/bin/env python
# -*- coding: utf-8 -*-
import config as CONFIG
import base64
import json
import re
import sys

from flask import Flask
from flask import render_template
from flask import send_file

if sys.version.find('2', 0, 1) == 0:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
else:
    from io import StringIO
    from io import BytesIO

# 必填且与plex对应

app = Flask(__name__)


@app.route("/")
@app.route("/index")
@app.route("/warning")
def warning():
    return render_template(
        'warning.html'
    )


@app.route("/img/<data>")
def img(data):
    data = json.loads(base64.b64decode(data))
    image = None
    for sourceList in CONFIG.SOURCE_LIST:
        for sourceItem in CONFIG.SOURCE_LIST[sourceList]:
            for spiderClass in sourceItem["webList"]:
                spider = spiderClass()
                if spider.getName().lower() == data['webkey'].lower():
                    image = spider.pictureProcessing(data)
    if image is not None:
        try:
            img_io = StringIO()
            image.save(img_io, 'PNG')
        except Exception:
            img_io = BytesIO()
            image.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpg')
    else:
        return ''


@app.route('/<requestType>/<dirTagLine>/<q>/<token>')
def getMediaInfos(requestType, dirTagLine, q, token):
    '''
    自动查询：返回最先成功的item
    '''
    if CONFIG.PLUGIN_TOKEN != '':
        if token != CONFIG.PLUGIN_TOKEN:
            return 'T-Error!'
    else:
        return 'T-Error!'

    q = base64.b64decode(q.replace('[s]', '/')).decode("utf-8")
    print(u'\n\n======开始请求======')
    if requestType == "manual":
        print(u'模式：手动')
        autoFlag = False
    elif requestType == "auto":
        print(u'模式：自动')
        autoFlag = True
    else:
        return 'URL-Error!'
    print(u'文件名：%s' % q)
    print(u'目录标记：%s' % dirTagLine)

    if dirTagLine != "" or not CONFIG.SOURCE_LIST[dirTagLine]:
        for template in CONFIG.SOURCE_LIST[dirTagLine]:
            # 循环模板列表
            codeList = re.findall(re.compile(template['pattern']), q)
            if len(codeList) == 0:
                continue
            # 对正则匹配结果进行搜索
            for code in codeList:
                items = search(template['webList'],
                               template['formatter'].format(code), autoFlag)
                if items.get("issuccess") == "true":
                    print("匹配数据结果：success")
                    print(u'======结束请求======')
                    print(u'======返回json======')
                    return json.dumps(items)
                else:
                    print("匹配数据结果：未匹配到结果")

    print(u'======结束请求======')
    print(u'======返回json======')
    return json.dumps({'issuccess': 'false', 'json_data': [], 'ex': ''})


def search(webList, q, autoFlag):
    """
    根据搜刮网站列表进行数据搜刮
    :param webList: 搜刮网站的List 类型应为 app.spider.BasicSpider 的子类
    :param q: 待匹配的文件名
    :param autoFlag: 自动表示 True 为开启，开启后仅返回搜索到的第一个结果 ，False 为关闭
    :return:
        未查询到example
        {
            'issuccess': 'false',
            'json_data': [],
            'ex': ''
        }
        查询到
        {
        'issuccess': 'true',
        'json_data': [some json data],
        'ex': ''
        }
    """

    print("格式化后的查询关键字：%s" % q)
    result = {
        'issuccess': 'false',
        'json_data': [],
        'ex': ''
    }
    for webSiteClass in webList:
        webSite = webSiteClass()
        items = webSite.search(q)
        for item in items:
            if item['issuccess']:
                result.update({'issuccess': 'true'})
                result['json_data'].append({webSite.getName(): item['data']})
                print("匹配关键字：%s  元数据来源站点：%s" % (q, webSite.getName()))
                if autoFlag:
                    return result
    return result


if __name__ == "__main__":
    app.run(
        host=CONFIG.HOST,
        port=CONFIG.PORT,
        debug=CONFIG.DEBUG
    )