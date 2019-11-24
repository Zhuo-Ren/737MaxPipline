# -*- coding: UTF-8 -*-
# 教程 https://www.cnblogs.com/awakenedy/articles/9182036.html
# 教程 https://docs.python.org/3/library/datetime.html#module-datetime

from sysdb import SysDb  # 数据库
from bingsearch import searchPeriod

# 起止日期  (2018, 10, 29)
startDay = (2018, 12, 1)  # 从此日期开始(包括此日期)
endDay = (2019, 1, 1)  # 到此日期结束(不包括此日期)
# 每天搜几个新闻
howManyNewsOneDay = 5
# 使用fiddler吗
certFile = None  # "./DO_NOT_TRUST_FiddlerRoot.crt"  # None

try:
    # 连接数据库
    SysDb.connectDataBase('./main.sqlite')

    # 初始化所有系统表
    SysDb.initAllSysTables(updateStrategy='continue')

    searchPeriod(startDay + endDay, howManyNewsOneDay, fiddler=certFile)

finally:
    SysDb.disconnectDataBase()
