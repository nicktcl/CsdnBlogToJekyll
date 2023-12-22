# 将csdn的博客爬取到本地并输出为jekyll可解析的markdown格式，同时保存博客的图片到本地

## 前言

在Github Pages搭建个人博客时利用 Jekyll 生成站点，Jekyll是一个静态站点生成器，可以根据Markdown文件自动生成静态的html文件。且Github Pages 支持托管jekyll。

因此我只要在本地编写符合Jekyll规范的Markdown文件，上传到Github上，Github Pages就会自动生成并托管整个网站。

我想把之前我CSDN上写的博客备份到本地，同时又可以上传到Github Pages搭建的个人博客，那么一个大问题就来了，如何将自己CSDN的博客批量导出并输出为jekyll可解析的markdown文章格式，并且将博客中的图片也保存到本地。

所以用python写了该脚本用于实现所需要的功能。



## 代码实现

爬取csdn的博客并批量输出为jekyll可以直接解析的markdown格式，对于每一篇文章，我们重点关注以下信息：

- 标题（title）
- 正文
- 发表时间（date）
- 所属类别（categories）
- 对应标签（tags）

括号中的英文就是jekyll下博客所需要的文件头格式标准，我们只需要将csdn中每一篇文章的上述属性爬取下来并以特定的格式写入文件即可。



### 所需要的包

```python
import os           
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

# 若要保存print出来的日志内容则加入下面两行
# mylog="mylog.log"
# sys.stdout = open(mylog,'w')

from lxml import etree
import requests
import html2text


from bs4 import BeautifulSoup
import codecs
import re

import imghdr   # 内置模块imghdr可以用来判断图片的真实类型。
import shutil   # 用于清空指定文件夹下所有文件
```



### request子程序

首先我们应该针对csdn的博客系统写一个通用的request函数（方法）：

```python
# request子程序
def request_get(url):
    session = requests.Session()

    headers = {
        'User-Agent': 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36'}
    response = requests.get(url, headers=headers, timeout=5)
    return response
```

这里的headers里面的信息是通过查看页面的审查元素信息找到的。

### 文章地址爬取子程序

该子程序依此爬取CSDN账号下的每一篇文章的地址，地址中包含id，然后再调用爬取单篇博客文章的子程序。

username为csdn的地址中的用户名。注意看每一行的注释。

```python
# 文章地址爬取子程序
def start_spider(username):
    # 把下面这个base_url换成你csdn的地址
    base_url = 'https://blog.csdn.net/' + username + '/'

    second_url = base_url + 'article/list/'
    # 从第一页开始爬取
    start_url = second_url + '1'

    number = 1      # 记录当前是第几个article_list
    count = 0       # 记录当前是第几篇文章

    # 开始爬取第一个article_list，返回信息在html中
    html = request_get(start_url)

    # 这个循环是对博客的article_list页面的循环
    while html.status_code == 200:          # 200说明request_get完成，这是因为http协议里面定义的状态码
        # 获取下一页的 url
        selector = etree.HTML(html.text)

        # cur_article_list_page[0]就是当前article_list页面中的文章的list
        cur_article_list_page = selector.xpath('//*[@id="mainBox"]/main/div[2]')
        d = cur_article_list_page[0].xpath('//*[@id="mainBox"]/main/div[2]/div[2]/h4/a')
        l = cur_article_list_page[0].findall('data-articleid')

        # 这个循环是对你每一个article_list中的那些文章的循环
        for elem in cur_article_list_page[0]:
            item_content = elem.attrib
            # 通过对比拿到的数据和网页中的有效数据发现返回每一个article_list中的list都有一两个多余元素，每个多余元素都有style属性，利用这一特点进行过滤
            if item_content.has_key('style'):
                continue
            else:
                if item_content.has_key('data-articleid'):
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


```



### 爬取单篇博客文章的子程序

按照拿到的每一个文章地址中的id对单篇文章进行爬取，并输出jekyll可解析的markdown文章格式，同时抓取博客中的图片保存到本地。注意看每一行的注释。

jekyll中markdown文件的头格式如下。

```markdown
    
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
```
```python
# 爬取单篇博客文章的子程序
def CrawlingItemBlog(base_url, id):
    second_url = base_url + 'article/details/'
    url = second_url + id
    # 发送request请求并接受返回值
    item_html = request_get(url)
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
        print(" 该篇博客标题为：" + file_name)
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
        time = soup.find(attrs={'class': 'time'}).get_text()
        s_time1 = time.split('年')
        year = s_time1[0]
        s_time2 = s_time1[1].split('月')
        month = s_time2[0]
        s_time3 = s_time2[1].split('日')
        day = s_time3[0]
        minite = s_time3[1].strip()

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


```

### 新建子文件夹程序

该子程序用于新建保存markdown文件和图片文件的文件夹。

```python
# 新建文件夹子程序
def mkdir(path):
    folder = os.path.exists(path)

    if not folder:  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(path)  # makedirs 创建文件时如果路径不存在会创建这个路径
        return True
    else:
        return False
```

### 主程序

```python
if __name__ == "__main__":
    username = 'Tang_Chuanlin'        # CSDN 个人主页地址中的用户名，例如https://blog.csdn.net/Tang_Chuanlin中的Tang_Chuanlin
    if os.path.exists('./imgs/'):      # 判断当前路径下是否存在"imgs"文件夹
        shutil.rmtree('./imgs/')       # 若存在，则删除该文件夹，目的是删除之前爬取获得的图片
    mkdir('./imgs/')                   # "imgs"新建文件夹
    if os.path.exists('./_posts/'):      # 判断当前路径下是否存在"_posts"文件夹
        shutil.rmtree('./_posts/')       # 若存在，则删除该文件夹，目的是删除之前爬取获得的markdown文件
    mkdir('./_posts/')                   # "_posts"新建文件夹
    print(" 开始爬取 " + username + " 的 CSDN 博客... ")
    start_spider(username)              # 开始爬取
    print('successful!')                # 因为是死循环一直爬取，所以一般需要手动停止
```



## 项目地址：

[CsdnBlogToJekyll](https://github.com/nicktcl/CsdnBlogToJekyll)，😝欢迎 star ，欢迎Fork! 




## 使用方法

- 在pycharm下运行，直接将工程下载到本地，将：

```python

if __name__ == "__main__":
    username = 'Tang_Chuanlin'        # CSDN 个人主页地址中的用户名，例如https://blog.csdn.net/Tang_Chuanlin中的Tang_Chuanlin
    if os.path.exists('./imgs/'):      # 判断当前路径下是否存在"imgs"文件夹
        shutil.rmtree('./imgs/')       # 若存在，则删除该文件夹，目的是删除之前爬取获得的图片
    mkdir('./imgs/')                   # "imgs"新建文件夹
    if os.path.exists('./_posts/'):      # 判断当前路径下是否存在"_posts"文件夹
        shutil.rmtree('./_posts/')       # 若存在，则删除该文件夹，目的是删除之前爬取获得的markdown文件
    mkdir('./_posts/')                   # "_posts"新建文件夹
    print(" 开始爬取 " + username + " 的 CSDN 博客... ")
    start_spider(username)              # 开始爬取
    print('successful!')                # 因为是死循环一直爬取，所以一般需要手动停止
    
```

中的username换成自己csdn的用户名，然后在pycharm下运行项目即可，因为是死循环一直爬取，所以一般需要手动停止。

项目运行完毕后markdown格式的文章会在“_posts”文件夹下，每篇博客的图片保存在“imgs”文件夹下。



- 在windows command窗口下直接运行时，需要先执行以下两条命令，将windows command窗口的编码改为utf-8。

  ```cmd
  chcp 65001
  ```

  ```cmd
  set PYTHONIOENCODING=utf-8
  ```

  然后再执行以下命令运行python脚本即可。

  ```cmd
  python export_csdn_markdown.py
  ```

  

gif动图中抓取过程中有一篇博客“解决You are using pip version 9.0.1, however version 9.0.3 is available. You should consider upgrading”保存图片时发错错误，可能是因为该篇博客标题过长，然后新建出的文件夹文件名过长，超出windows文件夹名长度的限制，所以发生了图片保存时的错误。

## 结语

至此就完成了将csdn的博客爬取到本地并输出为jekyll可解析的markdown格式，同时保存下了每一篇博客的图片到本地，然后将导出的markdown格式的文章（默认在“\_posts”目录下）放在jekyll博客目录的_posts文件夹下即可。

## 需要注意的问题

####  1、jekyll中post的markdown文件名格式如下：

2019-02-13-Beautiful Soup 4.2.0 官方中文文档.markdown

####  2、jekyll中post的markdown文件头格式如下：

    ---    layout:		post
    title: 		错误 Unable to locate package python-pip
    date: 		2019-02-14 15:10:56
    author:		"唐传林"
    header-img: 	"img/post-bg-2015.jpg"
    catalog:	 true
    tags:
    - python
    ---    

tags等关键字后面的冒号必须为英文冒号，为中文冒号jekyll编译生成的页面中该篇文章会没有文章标题、作者显示不对、日期不对等问题。  
tags下的标签不要添加空格或table。  
title下的字段不能带有英文或者中文冒号，title字段中带有中文冒号jekyll编译生成的页面中该篇文章会没有文章标题、作者显示不对、日期不对等问题。  
title中可带有单引号。

####  3、jekyll中post的markdown文件需要使用utf-8无BOM的编码，不能使用utf-8 BOM的编码。

爬虫保存的markdown文件默认为utf-8无BOM的编码，不用进行转换。csdn在线markdown编辑器导出的markdown文件默认为utf-8 BOM的编码，需要用notepad++进行转换一下。

####  4、爬虫保存的markdown文件中的图片链接

有些图片链接会换行，程序中已经对可能换行的图片链接进行了处理，若jekyll编译生成的页面中文章的图片不正常显示，则需要人工检查图片链接是否正常。

####  5、图片链接需要改为http协议

爬虫保存的markdown文件中的图片链接有些为http协议的，jekyll生成的页面中这种图片有些会显示不正常，所以图片链接最好改为http协议。程序中已经将图片链接中的https替换为了http。


####  5、执行报错`LookupError: unknown encoding: cp65001`

cmd执行报错`LookupError: unknown encoding: cp65001`， 执行`set PYTHONIOENCODING=UTF-8`

