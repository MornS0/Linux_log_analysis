### 说明
本人毕业设计->基于Linux日志信息的监控分析平台的设计与实现
由于第一次编写django项目，因此代码编写较烂，如果要了解其中的代码可能会费劲些...不过个人认为还是有一定的实用价值，有兴趣的可以跑跑看

### 功能总结
本课题致力于对Linux系统的日志进行分析，主要功能如下：

##### 对于管理员用户主要提供以下功能
1.添加服务器：管理员可以同时添加和管理多台服务器。
2.服务器概况：管理员可以查看所有添加的服务器概况信息，并可进入服务器分析结果页面查看。
3.管理控制台：对于添加的服务器，管理员可在此查看详细信息，并对服务器信息进行修改和删除操作，以及测试服务器可否连接，当连接有效，则可进行日志信息更新的一系列操作，同时也可进入服务器登录记录/异常记录/封禁名单/日志分析结果查看信息，以及进入命令行控制台对服务器进行远程操作。

##### 对于单个服务器，主要提供以下日志分析结果
1.登录记录：可以查看服务器至今的所有登录信息，包括：登录日期、登录时间、登出时间、使用时间、用户名、IP地址、地理位置、端口和登录类型（密码/密钥登录）。
2.异常记录：可以查看服务器进行的所有远程连接错误验证信息，包括：操作日期、IP地址、地理位置、错误认证次数和封禁情况。
3.IP封禁名单：可以查看服务器所有当前封禁的IP名单，包括：IP地址和地理位置。
4.日志分析结果：对分析的数据整合后进行可视化展示，包括：服务器日登录次数（柱状图）、服务器日总使用时间（折线图）和服务器登录IP地理位置分布图（地理图）。
5.对于以上的分析结果数据均提供下载。

##### 对于单个服务器，主要提供以下操作功能
1.命令行远程操作：在命令控制台界面将会与服务器进行远程连接，并提供管理员命令执行操作，其中命令行模式分为单命令模式和交互模式：单命令模式下将不保存之前命令的执行结果；交互模式将保存之前的命令执行结果。
2.IP封禁/解封操作：在异常记录和IP封禁名单当中可以进行IP封禁和解封操作，其中被封禁的IP将无法再与该服务器进行远程SSH连接。

### 功能配置
本课题利用了三个第三方接口，因此需要进行配置，具体如下：

##### IP138地理位置查询配置
1.进入官网：[链接](http://user.ip138.com/login)进行注册，并获取其中IP查询接口的校验信息
2.在项目中进行配置：
(1)在server_admin/static/js/log.js的41和44行添加对应的token、oid和mid信息
(2)在server_admin/static/js/log_ban.js的27和30行做同上配置
(3)在server_admin/static/js/record.js的3和5行做同上配置
(4)在server_receive/views.py的1007和1009行做同上配置


##### 百度基本定位配置
1.进入官网：[链接](http://lbsyun.baidu.com/apiconsole/key)，注册后创建一个包含普通IP定位的应用，获取AK值
2.在项目中进行配置：
(1)在server_receive/views.py的981行添加对应的AK值


##### 高德地图展示配置
1.进入官网：[链接](https://lbs.amap.com/api/javascript-api/guide/abc/prepare)进行注册
2.在项目中进行配置：
(1)在server_admin/templates/admin_view.html的75行配置高德地图JS API的key（这里已经配置好我的key了）
(1)在server_admin/templates/admin_geo.html的32行配置高德地图JS API的key（这里已经配置好我的key了）


### 部署步骤

1.配置好python（要求python3.0以上环境）和pip环境

2.执行requirement.txt下的命令安装相关模块

**注：**
其中pyecharts模块的安装可能会出现问题，此时下载文件：[文件地址](https://files.pythonhosted.org/packages/7e/aa/63f80d0d2d2ee43cfe9f30822eb751ba67359aa54507a05b740ed5666416/pyecharts-0.1.9.4-py2.py3-none-any.whl)，然后在该文件目录下打开命令行执行下面命令进行安装：
```
pip install pyecharts-0.1.9.4-py2.py3-none-any.whl
```

3.修改模块内容：

(1)pymysql模块：
在Python路径下的Lib\site-packages\django\db\backends\mysql\base.py文件中将下面两行注释：
```
if version < (1, 3, 13):
    raise ImproperlyConfigured('mysqlclient 1.3.13 or newer is required; you have %s.' % Database.__version__)
```
(2)pyecharts模块：
在Python路径下的Lib/site-packages/pyecharts/base.py文件中寻找到里面的show_config()函数，将该函数修改如下：
```
def show_config(self):
    """ Print all options of charts"""
    result = pformat(self._option)
    #把数据格式化后返回
    return result
```

4.安装mysql（要求5.6以上版本）log_analysis/settings.py下配置数据库信息：
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'log_analysis',
        # 数据库名称
        'USER': 'root',
        # 数据库账号
        'PASSWORD': '',
        # 数据库密码
        'HOST': '127.0.0.1',
        # 连接IP
        'PORT': '3306'
        # 连接端口
    }
}
```
5.在当前项目目录下输入以下命令完成数据表的创建：
```
python manage.py makemigrations
python manage.py migrate
```
6.执行下面的命令启动服务：
```
python manage.py runserver
```
7.（可选）配置Nginx环境，用于项目部署：

编辑Nginx根目录下的`/conf/nginx.conf`文件，加入以下代码：
```
upstream server1{  #新添一个upstream标签，自定义名称，最好不要有下划线
server 127.0.0.1:8000;  #服务器平台运行地址和端口
}
server {
    listen       80;	#监听端口
server_name  localhost;	#访问地址

    location / {
        root   html;
proxy_pass http://server1;	 #反向代理地址
index  index.html index.htm;
}
}
```
完成配置后，输入以下命令更新nginx服务器：
```
nginx -s reload
```

### 示例图片
部分结果展示如下：
##### 添加服务器
![](https://github.com/dawsonenjoy/log_analysis/tree/master/demo/add.jpg)
##### 控制台
![](https://github.com/dawsonenjoy/log_analysis/tree/master/demo/control.jpg)
##### 登录记录
![](https://github.com/dawsonenjoy/log_analysis/tree/master/demo/record.jpg)
##### 登录记录图
![](https://github.com/dawsonenjoy/log_analysis/tree/master/demo/view.jpg)
##### 登录地理图
![](https://github.com/dawsonenjoy/log_analysis/tree/master/demo/geo.jpg)
