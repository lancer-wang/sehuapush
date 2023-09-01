import re
import datetime
import json
import os
import random
from bs4 import BeautifulSoup
import pymysql,psycopg2
from lxml import etree

from playwright.sync_api import sync_playwright
import time


# 获取综合区等的内容
def get_content(page, web_url, url_type=1):
    try:
        page.goto(web_url)
        s = page.content()
        soup = BeautifulSoup(s, 'lxml')
        # AI区的页面和其他区有细微区别，2为AI区
        if url_type == 2:
            hostloc_content = soup.find_all("div", class_="pcb")[0]
        else:
            hostloc_content = soup.find_all("td", class_="t_f")[0]
        for tip in hostloc_content.find_all("div", class_="tip_4"):
            tip.decompose()
        for em in hostloc_content.find_all("em", class_="xg1"):
            em.decompose()
        contests = hostloc_content.text
        contests = contests.replace("\r\n", '').replace('\n', '').replace('\xa0', '').replace('\u200b', '')
        findal = re.findall(r'本帖最后由.*编辑', contests)
        if findal:
            contests = contests.replace(findal[0], "").lstrip()
        contests2 = contests
        return contests2
    except Exception as e:
        print(e)
        print("网络原因，无法访问，请稍后再试...")
        return "因权限或网络等原因，内容无法预览，请手动登陆查看！"


# 删掉换行等
def mark_down2(content):
    content = content.strip().replace("\n", "").replace('"', "'")
    return content


# 链接数据库
def get_db2():
    if dbtype == "pgsql":
        db2 = psycopg2.connect(database=dbname, user=user, password=password, host=host, port=port)
    elif  dbtype == "mysql":
        db2 = pymysql.Connect(host=host, port=port, user=user, passwd=password, db=dbname, charset="utf8mb4")
    else:
        print("数据库类型错误")
        exit()
    return db2

# 遍历帖子列表
def master(r, page, xpaths, url_type=1,tietype="综合区"):
    xml_content = etree.HTML(r)
    href_list = xml_content.xpath(
        '/html/body/div[' + xpaths + ']/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/th/a[2]/@href')
    author = xml_content.xpath(
        '/html/body/div[' + xpaths + ']/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/td[2]/cite/a/text()')
    number = xml_content.xpath(
        '/html/body/div[' + xpaths + ']/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/td[3]/a/text()')
    href = xml_content.xpath(
        '/html/body/div[' + xpaths + ']/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/th/a[2]/text()')
    href_2 = xml_content.xpath(
        '/html/body/div[' + xpaths + ']/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/th/a[3]/text()')
    for i in range(len(number)):
        href_id = href_list[i].split("tid=", )[-1].split("&", )[0]
        if not re.match(r'^\d+$', href_id):
            continue
        name = href[i].replace("\r\n", "")
        if name == "隐藏置顶帖":
            print("这是啥东西")
            continue
        print(str(name) + "id:" + str(href_id))
        # 判断是否为权限贴
        if name == "New":
            name = href_2[i].replace("\r\n", "")
        else:
            pass
        # 文章链接
        url_list = url_1 + "thread-{}-1-1.html".format(str(href_id))
        res = get_isset(url_list)
        if res == "123":
            continue
        # 作者id链接
        content_3 = get_content(page, url_list, url_type)
        try:
            insert_db(mark_down2(author[i]), url_list, mark_down2(name), mark_down2(content_3),tietype)
        except:
            print("插入失败")
            pass
        time.sleep(random.randint(5, 8))


# 获取配置
def get_con():
    if not os.path.exists("./982.json"):
        print("缺少配置文件")
        exit()
    else:
        f = open("./982.json", encoding="utf-8")
        res = f.read()
        f.close()
        config = json.loads(res)
        dbtype = str(config["db_type"])
        if config["db_type"] != "pgsql" or config["db_type"] != "mysql":
            print("请选择数据库")
            exit()
        if not re.match(r'^\d+$', str(config["times"])):
            config["times"] = 20
        if not re.match(r'^\d+$', str(config["timed"])):
            config["timed"] = 40
        if int(config["times"]) >= int(config["timed"]):
            config["times"] = 20
            config["timed"] = 40
        return dbtype,str(config[dbtype+"_host"]), str(config[dbtype+"_user"]), str(config[dbtype+"_dbname"]), str(config[dbtype+"_password"]),int(config[dbtype+"_port"]), int(config["times"]), int(
            config["timed"]), str(config["my_usename"]), str(config["my_pass"])
# 判断数据库是否有这个帖子
def get_isset(surl):
    db1 = get_db2()
    cursor1 = db1.cursor()
    select_from_toutiao_sql = """select surl  from omega_sehua_new where surl=%s"""
    cursor1.execute(select_from_toutiao_sql, (surl,))
    ras = cursor1.fetchall()
    cursor1.close()
    db1.close()
    # 更新表中使用不了的数据
    if len(ras) > 0:  # 表中已经存在
        print("已经存在")
        return '123'
    else:
        return "456"

# 添加进数据库
def insert_db(uname, surl, title, cont,tietype):
    db = get_db2()
    cursor = db.cursor()
    create_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    insert_sql = """insert into omega_sehua_new(uname, surl, title, cont, create_at,tietype) VALUES (%s,%s,%s,%s,%s,%s)"""
    cursor.execute(insert_sql, (uname, surl, title, cont, create_at,tietype))
    db.commit()
    cursor.close()
    db.close()
    print("数据添加成功")


# 全局配置
# 分别为 数据库类型,数据库host,数据库用户名，数据表名称，数据库密码，数据库端口，最短更新时间，最长更新时间，账号，密码
dbtype,host,user,dbname,password,port, times, timed, my_usename, my_pass = get_con()


headers = {
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
}
url_1 = "https://www.sehuatang.net/"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        # Open new page
        page = context.new_page()
    
        time.sleep(3)
        page.goto(url_1)
        time.sleep(5)
        # 网站的验证
        page.click('xpath=/html/body/a[1]')
        time.sleep(5)
        xpaths = "6"
        if my_usename != "" and my_pass != "":
            print("登陆")
            page.fill('xpath=//*[@id="ls_username"]',my_usename)
            page.fill('xpath=//*[@id="ls_password"]', my_pass)
            time.sleep(5)
            page.click('//*[@id="lsform"]/div/div/table/tbody/tr[2]/td[3]/button')
            time.sleep(5)
            xpaths = "7"
        try:
            qulist = ["166","141","95","142"]
            for ia in qulist:
                ## 综合区 95 转帖 142 AI 166 原创141
                range_num = 1000 # 除了ai区等基本都是最大1000页
                match ia:
                    case "95":
                        # 其他分区，按这种格式写即可
                        tietype = "综合区"
                    case "141":
                        tietype = "原创区"
                    case "166":
                        tietype = "AI区"
                        url_type = 2
                        range_num = 296 # 写代码的时候只有296页
                    case default:
                        tietype = "转帖交流区"
                for i in range(range_num, 0, -1):
                    print("当前id为"+ia+"页码为"+str(i))
                    url_sehua = url_1 + "forum.php?mod=forumdisplay&fid="+str(ia)+"&filter=author&orderby=dateline&page="+str(i)
                    page.goto(url_sehua)
                    master(page.content(), page, xpaths, url_type,tietype)
                    time.sleep(random.randint(3, 8))
        except Exception as e:
            print(e)
            print("网络错误，请稍后重试")
            time.sleep(random.randint(60, 90))

if __name__ == "__main__":
    main()
