import re
import datetime
import json
import os
import random
import sqlite3
from bs4 import BeautifulSoup
import pymysql,psycopg2,itertools
import requests
from lxml import etree

from playwright.sync_api import sync_playwright
import time


# 获取综合区等的内容
def get_content(page, web_url, url_type=1):
    try:
        page.goto(web_url)
        s = page.content()
        soup = BeautifulSoup(s, 'lxml')
        if url_type == 2:
            hostloc_content = soup.find_all("div", class_="pcb")[0]
        else:
            hostloc_content = soup.find_all("td", class_="t_f")[0]
        for tip in hostloc_content.find_all("div", class_="tip_4"):
            tip.decompose()
        img_list = hostloc_content.find_all("img", class_="zoom")
        # 遍历页面中的所有图片元素，将图片替换为 Markdown 格式
        for img in img_list:
            # 获取图片的 URL 地址
            if 'zoomfile' in img.attrs:
                img_url = img['zoomfile']
            elif 'file' in img.attrs:
                img_url = img['file']
            elif 'src' in img.attrs:
                img_url = img['src']
            else:
                img_url = ""

            # 将 img 元素替换为 Markdown 的图片语法
            markdown_img = "[图片](" + img_url + ")"
            img.replace_with(markdown_img)
        # 遍历页面中所有的附件元素
        # for link in hostloc_content.find_all('a'):
        #     # print(link.get_text())
        #     if link.name == 'a' and (link.get_text().endswith('.rar') or link.get_text().endswith('.7z') or link.get_text().endswith('.zip')):
        #         # 获取附件的 URL 地址
        #         link_url = mianfan_url + "/"+ link['href']
        #         # 将 a 元素替换为 Markdown 的附件语法
        #         markdown_link = "[" + link.get_text() + "](" + link_url + ")"
        #         # 将 a 元素替换为 Markdown 的附件语法
        #         link.replace_with(markdown_link)
        for em in hostloc_content.find_all("em", class_="xg1"):
            em.decompose()
        contests = hostloc_content.text
        contests = contests.replace("\r\n", '').replace('\n', '').replace('\xa0', '').replace('\u200b', '')
        findal = re.findall(r'本帖最后由.*编辑', contests)
        if findal:
            contests = contests.replace(findal[0], "").lstrip()

        pattern = r"\[图片\]\(.*?\)"
        # 用一个占位符替换[图片](url)
        placeholder = "#图"
        # 用一个列表来存储所有的[图片](url)
        images = re.findall(pattern, contests)
        # 用一个循环来替换所有的[图片](url)
        contests2 = contests
        for image in images:
            contests = contests.replace(image, placeholder, 1)
        contests3 = contests[0:100]
        if contests3.endswith("#"):
            contests3 = contests3 + "图"
        contests3 = mark_down(contests3)
        contests3 = contests3.replace("""\#图""", "#图 ")
        for image in images:
            contests3 = contests3.replace(placeholder, image, 1)
        return contests3, contests2
    except Exception as e:
        print(e)
        print("网络原因，无法访问，请稍后再试...")
        return "因权限或网络等原因，内容无法预览，请手动登陆查看！", "因权限或网络等原因，内容无法预览，请手动登陆查看！"


# ai区和综合区格式有差异


def mark_down(content):
    # 删除特殊符号，防止发生错误parse
    sign = ['&', '<', ".", '>', '?', '#', '%', '!', '@', '$', '^', '*', '(', ')', '-', '_', '+', '=',
            '~', '/', ',', ':', '’', '‘', '^', '{', '}', '[', ']', '`', "'", "|"]
    content = content.replace("\n", "")
    content = content.strip()
    for k in sign:
        content = content.replace(k, "\\" + k)
    return content


def mark_down2(content):
    content = content.strip().replace("\n", "").replace('"', "'")
    return content

# 是否登陆，在某些网站xpaths会发生变化
# 如果和我用的网站不同，请根据实际情况自行修改

def master(r, page, xpaths, url_type=1,tietype="综合区"):
    global mianfan_url
    global mianfan_url2
    # print(r)
    xml_content = etree.HTML(r)
    href_list = xml_content.xpath(
        '/html/body/div[' + xpaths + ']/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/th/a[2]/@href')
    author = xml_content.xpath(
        '/html/body/div[' + xpaths + ']/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/td[2]/cite/a/text()')
    author_url = xml_content.xpath(
        '/html/body/div[' + xpaths + ']/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/td[2]/cite/a/@href')
    number = xml_content.xpath(
        '/html/body/div[' + xpaths + ']/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/td[3]/a/text()')
    href = xml_content.xpath(
        '/html/body/div[' + xpaths + ']/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/th/a[2]/text()')
    href_2 = xml_content.xpath(
        '/html/body/div[' + xpaths + ']/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/th/a[3]/text()')
    for i in range(len(number)):
        if time.time() - t1 >= 86400:
            mianfan_url, mianfan_url2 = getmian(page)
        href_id = href_list[i].split("tid=", )[-1].split("&", )[0]
        if not re.match(r'^\d+$', href_id):
            continue
        isset = get_isset(href_id)
        if isset == "123":
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
        # 作者id链接
        url_author = url_1 + "{}".format(author_url[i])
        # uid = author_url[i].split(".")[0].split("=")[-1]
        uid = author_url[i].split("=")[-1]
        content_2, content_3 = get_content(page, url_list, url_type)
        mian_url = url_list.replace("https://www.sehuatang.net", mianfan_url)
        mian_url2 = url_list.replace("https://www.sehuatang.net", mianfan_url2)
        text = '\\[ 主        题 \\] ：' + "***{}***".format(
            mark_down(name)) + '\n' + '[{0}]       [{1}]({2})'.format(mark_down("#U" + uid),
                                                                      mark_down(author[i]),
                                                                      url_author) + '\n' + '\\[ 地        址 \\] ：[{0}]({1})     [{2}]({3})     [{4}]({5})'.format(
            str(href_id),
            url_list, "免翻地址", mian_url, "免翻地址2", mian_url2) + '\n' + '\\[ 内        容 ' \
                                                                             '\\] ：[ {} ]'.format(
            content_2)
        if url_type == 2:
            post(pid2, text)
        elif url_type == 1:
            post(pid, text)
        try:
            insert_db2(mark_down2(author[i]), url_list, mark_down2(name), mark_down2(content_3),href_id)
        except:
            print("插入失败")
            pass
        
        time.sleep(random.randint(5, 8))


# 发送到tg
def post(chat_id: str, text: str, silent: bool = False, num=0):
    try:
        with requests.post(
                url=f'https://api.telegram.org/bot{bottoken}/sendMessage',
                headers={
                    'Content-Type': 'application/json',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
                },
                data=json.dumps({
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': 'MarkdownV2',
                    'disable_notification': silent,
                    'disable_web_page_preview': True,
                })) as r:
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(e)
        print(text)
        print("推送失败！")
        if num > 10:
            return
        else:
            num += 1
        time.sleep(3)
        post(chat_id, text, num=num)


# 定时更新
t1 = 0


# 从json文件获取免翻
def getmian(page):
    global t1
    if not os.path.exists("./mianfan.json") or (t1 != 0 and time.time() - t1 >= 86400):
        file = open('./mianfan.json', 'w')
        mianfans = {}
        mianfans["t1"] = time.time()
        mianfans["mian_url1"], mianfans["mian_url2"] = get_mianfan(page)
        file.write(json.dumps(mianfans))
        file.close()
    else:
        f = open("./mianfan.json", encoding="utf-8")
        res = f.read()
        f.close()
        mianfans = json.loads(res)
    t1 = mianfans["t1"]
    return mianfans["mian_url1"], mianfans["mian_url2"]

# 由于某些原因，改为固定
def get_mianfan(page, mian_num=0):
    mian_url1 = "https://wpzo.app"
    mian_url2 = "https://xj4sds.com"
    return mian_url1,mian_url2
    try:
        link = "https://nux4n.cn/config.js" # 这个目前好像不安全
        page.goto(link)
        pattern = r"home_url\s*=\s*'([^']+)'"
        match = re.search(pattern, page.content())
        if match:
            mian_url1 = match.group(1)
            mian_url1 = mian_url1.rstrip('/')
        else:
            mian_url1 = "https://wpzo.app"
    except Exception as e:
        print(e)
        if mian_num > 10:
            mian_url1 = "https://wpzo.app"
            mian_url2 = "https://xj4sds.com"
            return mian_url1, mian_url2
        else:
            mian_num += 1
        time.sleep(3)
        get_mianfan(page, mian_num)
    return mian_url1, mian_url2


# 获取配置
def get_con():
    if not os.path.exists("./98.json"):
        print("缺少配置文件")
        exit()
    else:
        f = open("./98.json", encoding="utf-8")
        res = f.read()
        f.close()
        config = json.loads(res)
        if config["bottoken"] == "机器人token" or config["pid"] == "-100后面跟你的频道id":
            print("请填写配置文件")
            exit()
        if not re.match(r'^\d+$', str(config["times"])):
            config["times"] = 20
        if not re.match(r'^\d+$', str(config["timed"])):
            config["timed"] = 40
        if int(config["times"]) >= int(config["timed"]):
            config["times"] = 20
            config["timed"] = 40
        return str(config["bottoken"]), str(config["pid"]), str(config["pid2"]), int(config["times"]), int(
            config["timed"]), str(config["my_usename"]), str(config["my_pass"])


# 新增存到sqlite3
def get_db3():
    if not os.path.exists("sehua2.db"):
        con = sqlite3.connect("sehua2.db")
        cur = con.cursor()
        sql = """CREATE TABLE IF NOT EXISTS `sehua_new`  (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `uname` varchar(255)  NULL DEFAULT NULL,
  `surl` varchar(255)  NULL DEFAULT NULL,
  `title` varchar(255)  NULL DEFAULT NULL,
  `tid` varchar(255)  NULL DEFAULT NULL,
  `cont` text  NULL,
  `create_at` varchar(255)  NULL DEFAULT NULL
)"""
        cur.execute(sql)
        cur.close()
        con.close()
    con2 = sqlite3.connect("sehua2.db")
    return con2




def insert_db2(uname, surl, title, cont,tid):
    db = get_db3()
    cursor = db.cursor()
    create_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    insert_sql = """insert into sehua_new(uname, surl, title, cont, create_at,tid) VALUES ("{0}","{1}","{2}","{3}","{4}","{5}")""".format(
        uname, surl, title, cont, create_at,tid)
    cursor.execute(insert_sql)
    db.commit()
    cursor.close()
    db.close()
    print("数据添加成功")



def get_isset(tid):
    db1 = get_db3()
    cursor1 = db1.cursor()
    select_from_toutiao_sql = """select tid  from sehua_new where tid = "{0}" """.format(tid)
    cursor1.execute(select_from_toutiao_sql)
    ras = cursor1.fetchall()
    cursor1.close()
    db1.close()
    # 更新表中使用不了的数据
    if len(ras) > 0:  # 表中已经存在
        return '123'
    else:
        return "456"



# 全局配置
# 分别为机器人token,新帖频道，ai新帖频道，最短更新时间，最长更新时间，账号，密码
bottoken, pid, pid2, times, timed, my_usename, my_pass = get_con()


headers = {
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
}
# 可以改为其他镜像网站
# url_1 = "https://1uc82.com/"
url_1 = "https://www.sehuatang.net/"

mianfan_url, mianfan_url2 = "", ""

def main():
    global mianfan_url
    global mianfan_url2
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        # Open new page
        page = context.new_page()
        mianfan_url, mianfan_url2 = getmian(page)
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
            page.click('xpath=//*[@id="lsform"]/div/div/table/tbody/tr[2]/td[3]/button')
            time.sleep(5)
            xpaths = "7"
        # form_type = 3
        qulist = ["95","141","142","166","97"] ## 综合区 95 转帖 142 AI 166 原创141 资源出售区 97
        ## 用以无限循环
        qulist_cycle = itertools.cycle(qulist)
        while True:
            try:
                result = next(qulist_cycle)
                url_type = 1
                if result == "95":
                    tietype = "综合区"
                elif result == "141":
                    tietype = "原创区"
                elif result == "166":
                    tietype = "AI区"
                    url_type = 2
                elif result == "97":
                    tietype = "资源出售区"
                    url_type = 3
                else:
                    tietype = "转帖交流区"
                    url_type = 3
                print(tietype)
                ## 改为获取前两页，2改为其他数字就是前x页，注意不要大于1000
                for i in range(2, 0, -1):
                    print("当前页码为"+str(i))
                    url_sehua = url_1 + "forum.php?mod=forumdisplay&fid="+str(result)+"&filter=author&orderby=dateline&page="+str(i)
                    print("js验证")
                    # 网址
                    page.goto(url_sehua)
                    master(page.content(), page, xpaths, url_type,tietype)
                time.sleep(random.randint(times, timed))
            except Exception as e:
                print(e)
                print("网络错误，请稍后重试")
                time.sleep(random.randint(60, 90))

if __name__ == "__main__":
    main()
