# 教程 https://www.cnblogs.com/awakenedy/articles/9182036.html
# 教程 https://docs.python.org/3/library/datetime.html#module-datetime

import datetime3  # 日期
import time  # 睡觉
from sysdb import SysDb  # 数据库
import requests
import requestsplus  # 升级requests.get()的功能
from lxml import etree
import re
from readability import Document
from html2text import html2text
from indentation import indent  # 字符串缩进


# 搜索引擎
searchEngine = 'bing.com'  # 这个不能改，因为后边的完整url是定制的

# 起止日期（截止日期当天不搜）
startDate = datetime3.date(2018, 7, 1)
endDate = datetime3.date(2018, 8, 1)  # (2018, 8, 2)

# 每天搜几个新闻
howManyNewsOneDay = 5

# 使用fiddler吗
certFile = None  # "./DO_NOT_TRUST_FiddlerRoot.crt"  # None

try:
    # 连接数据库
    SysDb.connectDataBase('./main.sqlite')

    # 初始化所有系统表
    SysDb.initAllSysTables(updateStrategy='rewrite')

    # 循环中的当前日期
    curDate = startDate
    # 循环日期
    while curDate != endDate:
        # 计算URL
        delta = datetime3.date(2019, 11, 1) - curDate
        deltaNum = 18201 - delta.days
        print('搜素日期：', curDate)
        searchUrl = r"https://cn.bing.com/search?q=737max%e7%a9%ba%e9%9a%be&filters=ex1%3a%22ez5_" + \
            str(deltaNum) + "_" + str(deltaNum) + \
            r"%22&redir=2&frb=1&qpvt=737max%e7%a9%ba%e9%9a%be"
        print('搜索Url：', searchUrl)

        # 发送一个http请求并接收结果
        r = requests.getPlus(searchUrl, verify=certFile)
        # 判断http请求是否正确返回
        if r.status_code != 200:
            print('error：搜索页状态码异常')
            break
        # 获取返回html文本
        '''r.encoding = "utf-8"  # 因为是针对bing，我们知道编码肯定是utf-8'''
        searchHtml = r.text
        # 判断返回中是否有查询结果，判断是否被ban
        t = re.findall(r'条结果', searchHtml, re.I)
        if t == []:
            print('error：被ban了')
            break
        else:
            t = re.findall(r'\d+(?= 条结果)', searchHtml, re.I)
            t = t[0]
            print('搜索结果共几条：', t)
        # 解析searchHtml
        tree = etree.HTML(searchHtml)
        # 真正有效的新闻有几条（不算视频集和图片集）
        newsList = tree.xpath('/html/body[1]/div[1]/main[1]/ol[1]/li[@class="b_algo"]')
        newsNum = len(newsList)
        print('真正有效的新闻共几条：', newsNum)
        # 保存搜索页
        file = open("./corpora/" + searchEngine + '_' + str(curDate) + '.html', "wb")
        file.write(searchHtml.encode('utf-8'))
        file.close()

        # 循环(howManyNewsOneDay)条真正有效的新闻
        newsIndex = 0  # 注意是从1开始的,因为以上来就+=1(历史原因，懒得改了)
        howManyNewsSaved = 0
        while howManyNewsSaved < howManyNewsOneDay:
            newsIndex += 1
            # 如果总共都不够那么多条，那及时退出
            if newsIndex > newsNum:
                break
            print('  第%d个新闻' % newsIndex)

            # 取出当前新闻的相关信息
            news = newsList[newsIndex-1]
            titleElement = news.xpath('./h2/a')[0]
            newsUrl = titleElement.attrib['href']
            print('    网址：', newsUrl)
            newsTitle = titleElement.text
            print('    标题：', newsTitle)
            introduction = news.xpath('string(./div[1]/p[1])')
            print('    简介：', end='')
            print(indent(introduction, length=40, fIndent=0, lIndent=10))
            newsTime = re.findall(r'^\d+-\d+-\d+', introduction, re.I)[0]
            newsTimeYear = int(re.findall(r'^\d+(?=-)', newsTime, re.I)[0])
            newsTimeMonth = int(re.findall(r'(?<=-)\d+(?=-)', newsTime, re.I)[0])
            newsTimeDay = int(re.findall(r'(?<=-)\d+$', newsTime, re.I)[0])
            print('    发布时间：', newsTime)
            newsId = searchEngine + '_' + str(curDate) + '_' + str(newsIndex)
            print('    Id：', newsId)

            # 判断是否文字新闻，是否合格
            host = re.search('(?<=://)\S+?(?=/)', newsUrl).group()
            if host in ['www.yunjuu.com', 'v.qq.com', 'www.bilibili.com']:
                print('    新闻不合格，这个不算数')
                continue

            # 访问新闻网页
            # 发送一个http请求并接收结
            try:
                r = requests.getPlus(newsUrl, verify=certFile)
            except Exception as e:
                print('    这个新闻网站跪了，不算数：', e)
                continue
            # 获取返回html文本
            '''r.encoding = "utf-8"'''
            newsHtml = r.text
            # 去掉html中的回车和多余空格
            newsHtml = newsHtml.replace('\n', '')
            newsHtml = newsHtml.replace('  ', '')
            # 用readability抽取主要信息
            newsdoc = Document(newsHtml)
            newsTitle = newsdoc.title()
            print('    标题：', newsTitle)
            newsContentWithTags = newsdoc.summary()  # readability包的处理结果是带着html标签的
            # 去掉html标签，得到纯文本
            newsContent = html2text(newsContentWithTags)
            # 输出content
            print('    正文：', end='')
            print(indent(newsContent, length=40, fIndent=0, lIndent=10))

            # 判断是否文字新闻，是否合格
            if len(newsContent) < 200:
                print('    新闻不合格，这个不算数')
                continue

            # 插入数据库
            SysDb.insertRow(
                'websiteTabel',
                {
                    '搜索引擎': searchEngine,
                    '搜索日期年': curDate.year,
                    '搜索日期月': curDate.month,
                    '搜索日期日': curDate.day,
                    '搜索网址': searchUrl,
                    '搜索html': searchHtml,
                    '新闻序号': newsIndex,
                    '新闻ID': newsId,
                    '新闻网址原': newsUrl,
                    '新闻网址真': r.url,
                    '新闻html': newsHtml,
                    '新闻标题': newsTitle,
                    # '新闻作者': {'类型': '文本', '初始值': None, '主键否': '非主键'},
                    # '新闻机构': {'类型': '文本', '初始值': None, '主键否': '非主键'},
                    '新闻日期年': newsTimeYear,
                    '新闻日期月': newsTimeMonth,
                    '新闻日期日': newsTimeDay,
                    '新闻正文': newsContent
                }
            )
            # 保存了一个，计数加一
            howManyNewsSaved += 1
        # curDate++
        curDate = curDate + datetime3.timedelta(1)
        del r, searchHtml, tree

        # 睡一会
        time.sleep(2)
        print('zzz')

finally:
    SysDb.disconnectDataBase()
