#!/usr/bin/env python2.7
# coding=utf-8

import re
import os           # 多种操作系统接口：该模块提供了一种使用操作系统相关功能的便携方式。
import sys          # 系统特定的参数和功能：该模块提供对解释器使用或维护的一些变量的访问，以及与解释器强烈交互的函数。
# 在程序中加入以下代码：将编码设置为utf8
reload(sys)
sys.setdefaultencoding("utf-8")

# 若要保存print出来的日志内容则加入下面两行
# mylog="mylog.log"
# sys.stdout = open(mylog,'w')

from lxml import etree  # 结构化标记处理工具：提供解析xml的相关操作
import requests         # Requests是一个用Python编写的Apache2许可HTTP库，用于发送HTTP请求。Python的内置urllib2模块提供了您应该需要的大多数HTTP功能，但非常冗长和繁琐。
import html2text        # 它将HTML页面转换为干净，易于阅读的纯ASCII文本，用于将html中所需要的内容解析为文本


from bs4 import BeautifulSoup   # Beautiful Soup是一个可以轻松从网页上抓取信息的库。它位于HTML或XML解析器的顶部，提供Pythonic习语用于迭代，搜索和修改解析树。
import codecs                   # 编解码器注册表和基类：该模块定义了标准Python编解码器（编码器和解码器）的基类，并提供对内部Python编解码器注册表的访问，该注册表管理编解码器和错误处理查找过程。
import re                       # 提供正则表达式操作：此模块提供与Perl中类似的正则表达式匹配操作。要搜索的模式和字符串都可以是Unicode字符串以及8位字符串。

import imghdr   # 内置模块imghdr可以用来判断图片的真实类型。
import shutil   # 用于清空指定文件夹下所有文件


# request请求子程序
def request_get(url):

    headers = {
        'User-Agent': 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36'}
    response = requests.get(url, headers=headers, timeout=5)
    return response


# 新建文件夹子程序
def mkdir(path):
    folder = os.path.exists(path)

    if not folder:  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(path)  # makedirs 创建文件时如果路径不存在会创建这个路径
        return True
    else:
        return False


# 爬取单篇博客文章的子程序，id为当前文章的id
def CrawlingItemBlog(base_url, id):
    second_url = base_url + 'article/details/'
    url = second_url + id
    # 发送request请求并接受返回值
    item_html = request_get(url)
    print("---", url)
    if item_html.status_code == 200:    # 200说明request_get完成，这是因为http协议里面定义的状态码
        '''
        需要的信息：
        1：标题
        2：markdown内容
        3：发表日期
        4：标签
        5：类别
        
        jekyll中markdown文件的头格式
        ---
            layout:     post
            title:      ""
            date:       2018-03-08 12:41:47
            author:     "Nick"
            header-img: "img/post-bg-2015.jpg"
            catalog: true
            tags:
                - 电脑技巧
        ---
        '''

        # 利用BeautifulSoup解析返回的html
        soup = BeautifulSoup(item_html.text, "lxml")
        # 筛选出博客正文那一部分html
        c = soup.find(id="content_views")

        # 标题
        title_article = soup.find(attrs={'class': 'title-article'})
        # 这里是将标题作为最后存储的文件名
        file_name = title_article.get_text()
        print(" 该篇博客标题为：" + file_name.encode("utf-8"))
        title_article = title_article.prettify()

        # 设置jekyll格式博客开头的格式（title）
        jekyll_title = 'title:   ' + file_name + '\n'

        # 文章的categories
        jekyll_categories = ''

        # 有可能出现这篇文章没有categories的情况
        try:
            jekyll_categories = soup.find(attrs={'class': 'tags-box space'}).find(attrs={'class': 'tag-link'}).get_text()
        except Exception:
            pass

        if jekyll_categories == '':
            pass
        else:
            # 去除拿到的str中的'\t'
            jekyll_categories = jekyll_categories.replace('\t', '')
            jekyll_categories = 'categories:\n' + '- ' + jekyll_categories + '\n'

        # 获取文章发表时间
        
        time = soup.find(attrs={'class': 'time'}).text
     
        time = re.match(".*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*", time).group(1)
        print(time, "9999999")
        s_time0 = time.split(' ')
        s_time1 = s_time0[0].split('-')
       
        
        year = s_time1[0]
        month = s_time1[1]
        day = s_time1[2]
        minite = s_time0[1].split(':')[1]
        print(s_time1, "1111000000")

        jekyll_date = 'date:   ' + year + '-' + month + '-' + day + ' ' + minite + '\n'

        jekyll_tags = ''

        # 获取tags标签
        tags = ''
        try:
            tags = soup.find(attrs={'class': 'tags-box artic-tag-box'}).get_text()
        except Exception:
            pass

        if tags == '':
            pass
        else:
            tags = tags.split('\n')
            tags = tags[2]
            tags = tags.replace('\t', ' ')
            tags = tags.split(' ')
            jekyll_tags = 'tags:\n'
            for tag in tags:
                if tag == '':
                    continue
                else:
                    jekyll_tags = jekyll_tags + '- ' + tag + '\n'

        # 将html转化为markdown
        text_maker = html2text.HTML2Text()
        text_maker.bypass_tables = False
        text = text_maker.handle(c.prettify())

        # 通过html2text转换得到的markdwon文本中'img-'后面会有一个换行符，导致图片链接不正确
        # 更正转换得到的markdown文件中'img-\n'为'img-'，即删除'img-'后面的换行符
        text_utf8 = text.encode('utf-8')
        text_utf8 = text_utf8.replace('-\n', '-')
        text_utf8 = text_utf8.replace('\n]', ']')
        text_utf8 = text_utf8.replace('\n/', '/')
        text_utf8_right = text_utf8.replace('https', 'http')
        # text_utf8_right = text_utf8.replace('?x-oss-\n', '?x-oss-')
        # print(text_utf8_right)
        text_utf8_right = text_utf8_right.replace('(//img-blog', '(http://img-blog')

        # 有的文章名字特殊，会新建文件失败
        try:
            # 写入文件
            md_file_name = './_posts/' + year + '-' + month + '-' + day + '-' + file_name + '.markdown'
            f = codecs.open(md_file_name, 'w', encoding='utf-8')
            jekyll_str = '---\n' + 'layout:  post\n' + jekyll_title + jekyll_date + 'author:  "唐传林"\nheader-img: "img/post-bg-2015.jpg"\ncatalog:   false\n' + jekyll_categories + jekyll_tags + '\n---\n'

            f.write(jekyll_str)
            f.write(text_utf8_right)
            f.close()
        except Exception:
            print(' 写入文件 ' + file_name + ' 出错. ')


        # 若不爬取图片保存下来，则该CrawlingItemBlog子程序中以下这一小段到return True之前可以删除或者注释，可提高爬取博客的速度
        # 爬取每篇博客的图片保存下来是为了给博客做备份，万一哪天csdn挂了

        # 获取当前该篇博客中所有图片的地址
        all_img = c.find_all('img')
        # print(all_img)
        k = 1 # 当前该篇博客的图片序号，从1开始
        # 遍历每一张图片并保存下来
        for img in all_img:     # 能进入该循环则说明该篇博客中有图片
            # 若该篇博客中有图片，则以该篇博客的title创建文件夹，
            if k == 1:
                folder_path = './imgs/' + year + '-' + month + '-' + day + '-' + file_name
                mkdir(folder_path)
            # <class 'bs4.element.Tag'>转string
            img_str = str(img)
            '''
            csdn博客页面中 img 地址有以下6种情况：
            1、<img alt="在这里插入图片描述" src="https://img-blog.csdn.net/20180403152931142?watermark/2/text/aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L1RhbmdfQ2h1YW5saW4=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70"/>
            2、<img alt="在这里插入图片描述" src="https://img-blog.csdnimg.cn/20190208181833408.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L1RhbmdfQ2h1YW5saW4=,size_16,color_FFFFFF,t_70"/>
            3、<img alt="在这里插入图片描述" src="https://img-blog.csdnimg.cn/2019011319584747.jpg?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L1RhbmdfQ2h1YW5saW4=,size_16,color_FFFFFF,t_70"/>
            4、<img alt="在这里插入图片描述" src="https://img-blog.csdnimg.cn/20190214214731928.jpg"/>
            5、<img alt="在这里插入图片描述" src="https://img-blog.csdnimg.cn/20190113200938989.gif"/>
            6、<img alt="在这里插入图片描述" src="https://img-blog.csdnimg.cn/20190108161409240.png"/>
            
            为了去除csdn图片的水印，图片地址?后面的东西不要，则获得的图片是无水印的
            '''
            # re.findall中的参数需要为string，正则表达式搞了好久才搞对，在notepad++里面测试没问题的在python下有问题，
            img_url = re.findall(r"(?=img-blog).*?(?:\?|jpg|gif|png)", img_str)
            # img_url = re.findall(r"(?=img-blog).*?(?=\?)", img_str)     # 该正则表达式只能找到第1、2、3种img地址的情况
            # print('img_str: ' + img_str)
            # print('img_url: ' + str(img_url))
            img_url_str = "".join(img_url)      # list转string
            # print('img_url_str' + img_url_str)
            try:
                # 下载图片暂时存盘为jpg格式
                ir = requests.get('https://' + img_url_str)
                img_name =  'temp.jpg'  # 临时文件名
                if ir.status_code == 200:       # 200说明request_get完成，这是因为http协议里面定义的状态码
                    open(img_name , 'wb').write(ir.content)     # 存盘
                # 判断图片真实格式并重命名改后缀为真实格式
                img_real_name = folder_path + "/" + year + '-' + month + '-' + day + '-' + file_name + "_图" + str(k) +  "." + imghdr.what(img_name)        # imghdr.what(img_name)用来判断图片真实格式
                os.rename(img_name, img_real_name)      # os.rename对图片进行重命名
                k = k + 1       # 当前该篇博客的图片序号递增1
            except Exception:
                print(" 获取博客“" + file_name + "”的图片时出现错误...\t\t正则表达式之前图片地址：http://" + img_str)
        return True
    else:
        return False


# 文章地址爬取子程序
def start_spider(username):
    # 把下面这个base_url换成你csdn的地址
    base_url = 'https://blog.csdn.net/' + username + '/'

    second_url = base_url + 'article/list/'
    # 从第一页开始爬取
    start_url = second_url + '1'

    number = 1      # 记录当前是第几个article_list
    count = 0       # 记录当前是第几篇文章
    print(start_url)
    # 开始爬取第一个article_list，返回信息在html中
    html = request_get(start_url)
    print("html", html)   
    # 这个循环是对博客的article_list页面的循环
    while html.status_code == 200:          # 200说明request_get完成，这是因为http协议里面定义的状态码
        # 获取下一页的 url
        selector = etree.HTML(html.text)

        #print(html.text.encode("utf-8"))
        # cur_article_list_page[0]就是当前article_list页面中的文章的list
        cur_article_list_page = selector.xpath('//*[@id="articleMeList-blog"]/div[2]/div')
        # cur_article_list_page = '//*[@id="articleMeList-blog"]/div[2]/div'
        #d = selector2.xpath('//*[@id="mainBox"]/main/div[2]/div[2]/div/h4/a')
        #print(d)
#        l = selector.findall('[data-articleid]')
        #l = selector3.xpath('//*[@id="articleMeList-blog"]/div[2]/div')

        # 这个循环是对你每一个article_list中的那些文章的循环
        for elem in cur_article_list_page:
            
            item_content = elem.attrib
            print(item_content)
            # 通过对比拿到的数据和网页中的有效数据发现返回每一个article_list中的list都有一两个多余元素，每个多余元素都有style属性，利用这一特点进行过滤
            if item_content.has_key('style'):
                continue
            else:
                if item_content.has_key('data-articleid'):
                    print(item_content)
                    # 拿到文章对应的articleid
                    articleid = item_content['data-articleid']
                    # 用于打印进度
                    count += 1
                    print("\n 找到第" + str(count) + "篇博客，正在处理...")
                    # 爬取单篇文章
                    CrawlingItemBlog(base_url, articleid)

        # 进行下一article_list的爬取
        number += 1
        next_url = second_url + str(number)
        html = request_get(next_url)


if __name__ == "__main__":
    username = 'jioulongzi'        # CSDN 个人主页地址中的用户名，例如https://blog.csdn.net/Tang_Chuanlin中的Tang_Chuanlin
    if os.path.exists('./imgs/'):      # 判断当前路径下是否存在"imgs"文件夹
        shutil.rmtree('./imgs/')       # 若存在，则删除该文件夹，目的是删除之前爬取获得的图片
    mkdir('./imgs/')                   # "imgs"新建文件夹
    if os.path.exists('./_posts/'):      # 判断当前路径下是否存在"_posts"文件夹
        shutil.rmtree('./_posts/')       # 若存在，则删除该文件夹，目的是删除之前爬取获得的markdown文件
    mkdir('./_posts/')                   # "_posts"新建文件夹
    print(" 开始爬取 " + username + " 的 CSDN 博客... ")
    start_spider(username)              # 开始爬取
    print('successful!')                # 因为是死循环一直爬取，所以一般需要手动停止