"""log_analysis URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include
from user_admin import views
from django.conf import settings

from django.conf.urls import url
from django.conf.urls.static import static

from apscheduler.scheduler import Scheduler  
# 定时任务
  
from server_receive.views import connect_check_thread, connect_get_thread
sched = Scheduler()
#实例化，固定格式
 
@sched.interval_schedule(seconds=18)
#装饰器，seconds=60意思为该函数为1分钟运行一次
def mytask(): 
    print("自动更新开始...")
    connect_check_thread()
    connect_get_thread()
  
sched.start()
#启动该脚本

# def prod_static_url():
#     '''
#     prod 模式下的 url 适配
#     '''
#     from django.views import static
#     urlpattern = url(r'^static/(?P<path>.*)$', static.serve, {'document_root': settings.STATIC_ROOT }, name='static')
#     return urlpattern


urlpatterns = [
    path('', views.index),
    path('get_code/', views.get_code),
    # 获取验证码
    path('index/', views.index),
    # 主页
    path('instr/', views.instr),
    # 说明
    path('regist/', views.regist),
    # 注册
    path('regist_deal/', views.regist_deal),
    # 注册验证
    path('regist_judge/', views.regist_judge),
    # 注册信息判断
    path('login/', views.login),
    # 登录
    path('login_deal/', views.login_deal),
    # 登录验证
    path('logout/', views.logout),
    # 登出
    path('forget/', views.forget),
    # 忘记密码
    path('forget_deal/', views.forget_deal),
    # 找回密码验证
    path('admin/', include('server_admin.urls')),
    # 管理员相关操作
    path('admin/receive/', include('server_receive.urls')),
    # 接收数据相关操作
    # prod_static_url()
]# + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# handler404 = views.index

