# -*- encoding: utf-8 -*-
# 自行百度安装chrome和chromedriver
# 配置文件中分别添加机器人的bot token（从bot father获取）和 频道id（格式为-100 后面跟频道信息中的id）
# 注意修改底部的chromedriver路径
import datetime
import json
import os
import random
import re
import sqlite3
import time
from bs4 import BeautifulSoup
import requests
from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
# 国内vps 需使用代理进行推送
# 以及把url_1 改为国内（服务器）可访问的镜像地址
proxies = {} # 举例 proxies = {"http": "http://127.0.0.1:123456"}
url_1 = "https://www.sehuatang.net/"

# 可以改为其他分区或者多个分区，仿造底部格式更改即可


def get_content(web_url,url_type=1):
    try:
        browser.get(web_url)
        s = browser.page_source
        # s = re.sub(r'<div class="tip tip_4 aimg_tip">.*?</div>', '', s, flags=re.I | re.M)
        soup = BeautifulSoup(s, 'lxml')
        if url_type ==2:
            hostloc_content = soup.find_all("div", class_="pcb")[0]
        else:
            hostloc_content = soup.find_all("td", class_="t_f")[0]
        for tip in hostloc_content.find_all("div", class_="tip_4"):
            tip.decompose()
        img_list = hostloc_content.find_all("img", class_="zoom")
        # 遍历页面中的所有图片元素，将图片替换为 Markdown 格式
        for img in img_list:
            # 获取图片的 URL 地址
            try:
                if img['zoomfile']:
                    img_url = img['zoomfile']
                elif img['file']:
                    img_url = img['file']
                else:
                    img_url = img['src']
            except Exception as e:
                print(e)
                img_url = img['src']
            # 将 img 元素替换为 Markdown 的图片语法
            markdown_img = "[图片](" + img_url + ")"
            img.replace_with(markdown_img)
        # 遍历页面中所有的附件元素
        for link in hostloc_content.find_all('a'):
            print(link.get_text())
            if link.name == 'a' and (link.get_text().endswith('.rar') or link.get_text().endswith('.7z') or link.get_text().endswith('.zip')):
                # 获取附件的 URL 地址
                link_url = mianfan_url + "/"+ link['href']
                # 将 a 元素替换为 Markdown 的附件语法
                markdown_link = "[" + link.get_text() + "](" + link_url + ")"       
                # 将 a 元素替换为 Markdown 的附件语法
                link.replace_with(markdown_link)
        for em in hostloc_content.find_all("em", class_="xg1"):
            em.decompose()
        contests = hostloc_content.text
        contests= contests.replace("\r\n", '').replace('\n', '').replace('\xa0', '').replace('\u200b', '')
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
        contests= contests[0:100]
        if contests.endswith("#"):
            contests+"图"
        contests = mark_down(contests)
        contests = contests.replace("""\#图""","#图 ")
        for image in images:
            contests = contests.replace(placeholder, image, 1)
        return contests, contests2
    except Exception as e:
        print(e)
        print("网络原因，无法访问，请稍后再试...")
        return "因权限原因，内容无法预览，请手动登陆查看！"


def mark_down(content):
    # 删除特殊符号，防止发生错误parse
    sign = ['&', '<', ".", '>', '?', '#', '%', '!', '@', '$', '^', '*', '(', ')', '-', '_', '+', '=',
            '~', '/', ',', ':', '’', '‘', '^', '{', '}', '[', ']', '`', "'","|"]
    content = content.replace("\n", "")
    content = content.strip()
    for k in sign:
        content = content.replace(k, "\\" + k)
    return content
def mark_down2(content):
    content = content.strip().replace("\n", "").replace('"', "'")
    return content

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
                }),
                proxies=proxies
                ) as r:
            r.raise_for_status()
            return r.json()
    except Exception:
        print("推送失败！")
        if num > 10:
            return
        else:
            num += 1
        time.sleep(3)
        post(chat_id, text, num=num)


# 主程序
def master(r,url_type=1):
    global t1 
    global mianfan_url
    global mianfan_url2
    xml_content = etree.HTML(r)
    href_list = xml_content.xpath('/html/body/div[6]/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/th/a[2]/@href')
    author = xml_content.xpath('/html/body/div[6]/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/td[2]/cite/a/text()')
    author_url = xml_content.xpath(
        '/html/body/div[6]/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/td[2]/cite/a/@href')
    number = xml_content.xpath('/html/body/div[6]/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/td[3]/a/text()')
    href = xml_content.xpath('/html/body/div[6]/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/th/a[2]/text()')
    href_2 = xml_content.xpath('/html/body/div[6]/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/th/a[3]/text()')
    # print(author)
    # print(number)
    tie_list2 = tie_list[-300:]
    have_new = 0
    for i in range(len(number)):
        if time.time() - t1 >= 86400:
            mianfan_url,mianfan_url2 = get_mianfan()
            t1 = time.time()
        href_id = href_list[i].split("tid=", )[-1].split("&", )[0]
        if not re.match(r'^\d+$', href_id):
            continue
        if str(href_id) not in tie_list2:
            have_new = 1
            tie_list.append(str(href_id))
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
            uid = author_url[i].split(".")[0].split("-")[-1]
            content_2, content_3 = get_content(url_list,url_type)
            mian_url = url_list.replace("https://www.sehuatang.net",mianfan_url)
            mian_url2 = url_list.replace("https://www.sehuatang.net",mianfan_url2)
            
            text = '\\[ 主        题 \\] ：' + "***{}***".format(
                mark_down(name)) + '\n' + '[{0}]       [{1}]({2})'.format(mark_down("#U"+uid),
                mark_down(author[i]),
                url_author) + '\n' + '\\[ 地        址 \\] ：[{0}]({1})     [{2}]({3})     [{4}]({5})'.format(str(href_id),
                                                                               url_list,"免翻地址",mian_url,"免翻地址2",mian_url2) + '\n' + '\\[ 内        容 ' \
                                                                                                  '\\] ：[ {} ]'.format(
                content_2)
            # print(text)
            
            post(pid, text)
            try:
                insert_db2(mark_down2(author[i]), url_list, mark_down2(name), mark_down2(content_3))
            except:
                print("插入失败")
                pass
        else:
            pass
        time.sleep(random.randint(5, 8))
    if have_new == 1:
        add_list(tie_list[-300:])

## 新增添加到数据库
def get_db3():
    if not os.path.exists("sehua.db"):
        con = sqlite3.connect("sehua.db")
        cur = con.cursor()
        sql = """CREATE TABLE IF NOT EXISTS `sehua_new`  (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `uname` varchar(255)  NULL DEFAULT NULL,
  `surl` varchar(255)  NULL DEFAULT NULL,
  `title` varchar(255)  NULL DEFAULT NULL,
  `cont` text  NULL,
  `create_at` varchar(255)  NULL DEFAULT NULL
)"""
        cur.execute(sql)
        cur.close()
        con.close()
    con2 = sqlite3.connect("sehua.db")
    return con2
def insert_db2(uname, surl, title, cont):
    db = get_db3()
    cursor = db.cursor()
    create_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    insert_sql = """insert into sehua_new(uname, surl, title, cont, create_at) VALUES ("{0}","{1}","{2}","{3}","{4}")""".format(uname, surl, title, cont, create_at)
    cursor.execute(insert_sql)
    db.commit()
    cursor.close()
    db.close()
    print("数据添加成功")

def get_list():
    if not os.path.exists("./tielist.json"):
        file = open('./tielist.json', 'w')
        sehua_list = ["1035238", "1028441"]
        file.write(json.dumps(sehua_list))
        file.close()
    else:
        f = open("./tielist.json", encoding="utf-8")
        res = f.read()
        f.close()
        sehua_list = json.loads(res)
    return sehua_list


def add_list(content):
    f = open('./tielist.json', 'w')
    f.write(json.dumps(content))
    f.close()


# 读取配置文件
def get_con():
    if not os.path.exists("./98.json"):
        print("缺少配置文件")
        exit()
    else:
        f = open("./98.json", encoding="utf-8")
        res = f.read()
        f.close()
        config = json.loads(res)
        if config["bottoken"] == "机器人token" or config["pid"] == "-100后面跟你的频道id" or config["executable_path"] == "你的chromedriver路径":
            print("请填写配置文件")
            exit()
        if not re.match(r'^\d+$', str(config["times"])):
            config["times"] = 20
        if not re.match(r'^\d+$', str(config["timed"])):
            config["timed"] = 40
        if int(config["times"]) >= int(config["timed"]):
            config["times"] = 20
            config["timed"] = 40
        return str(config["bottoken"]), str(config["pid"]),str(config["executable_path"]),int(config["times"]),int(config["timed"])


# 获取配置
bottoken, pid ,executable_path,times,timed= get_con()
# 获取已经发送的帖子列表
tie_list = get_list()
headers = {
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
}

c_service = Service(executable_path)
c_service.command_line_args()
c_service.start()
c_options = Options()
# 无界面浏览器
c_options.add_argument('--no-sandbox')
c_options.add_argument('--headless')
c_options.add_argument('--disable-gpu')
browser = webdriver.Chrome(service=c_service, options=c_options)

def get_mianfan(mian_num=0):
    mian_url1 = "https://www.dkxs12.com"
    mian_url2 = "www.xj4sds.com"
    try:
        link = "https://nux4n.cn/config.js"
        browser.get(link)
        # print(f.text)
        pattern = r"home_url\s*=\s*'([^']+)'"
        pattern2 = r"share_url\s*=\s*'([^']+)'"
        match = re.search(pattern, browser.page_source)
        match2 = re.search(pattern2, browser.page_source)
        if match:
            mian_url1 = match.group(1)
            mian_url1 = mian_url1.rstrip('/')
        else:
            mian_url1 = "https://www.dkxs12.com"
        if match2:
            try:
                share_url = match2.group(1)
                browser.get(share_url)
                time.sleep(20)
                url2 = browser.current_url
                mian_url2 = url2.replace("/?iframe=ios","")
            except Exception as e:
                print(e)
                mian_url2 = "www.xj4sds.com"
        else:
            mian_url2 = "www.xj4sds.com"
    except Exception as e:
        print(e)
        if mian_num > 10:
            mian_url1 = "https://www.dkxs12.com"
            mian_url2 = "www.xj4sds.com"
            return mian_url1,mian_url2
        else:
            mian_num += 1
        time.sleep(3)
        get_mianfan(mian_num)
    return mian_url1,mian_url2
t1 = time.time()
mianfan_url,mianfan_url2 = get_mianfan()

# 网站的验证
browser.get(url_1)
time.sleep(5)
browser.find_element(By.XPATH,'/html/body/a[1]').click()
form_type = '1'
while True:
    try:
        url_type = 1
        if form_type == "1":
            print("综合区")
            url_sehua = url_1 + "forum.php?mod=forumdisplay&fid=95&filter=author&orderby=dateline"
            form_type = "2"
        else:
            print("原创区")
            url_sehua = url_1 + "forum.php?mod=forumdisplay&fid=141&filter=author&orderby=dateline"
            form_type = "1"
            # case 3:
            #     print("AI区")
            #     url_sehua = url_1 + "forum.php?mod=forumdisplay&fid=166&filter=author&orderby=dateline"
            #     url_type = 2
        # # 网站不要求js验
        # r = requests.get(url_sehua, headers=headers)
        # xml_content = etree.HTML(r.content)
        # href_list = xml_content.xpath(
        #     '/html/body/div[6]/div[6]/div/div/div[4]/div[2]/form/table/tbody/tr/th/a[2]/@href')
        # if href_list:
        #     a = 2
        #     print(a)
        #     master(r.content)
        #     time.sleep(random.randint(14, 24))
        # else:
        # a = 1
        print("js验证")
        # 网址
        browser.get(url_sehua)
        master(browser.page_source,url_type)
        # browser.quit()
        # c_service.stop()
        time.sleep(random.randint(times, timed))
    except Exception:
        print("网络错误，请稍后重试")
        time.sleep(random.randint(60, 90))
