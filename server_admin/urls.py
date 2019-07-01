from django.urls import path
from . import views

urlpatterns = [
	# path('', views.index, name='index'),
    path('', views.admin, name='admin'),
    # 管理员信息
    path('change/', views.change, name='change'),
    # 修改信息
    path('change_deal/', views.change_deal, name='change_deal'),
    # 修改信息验证
    path('switch/', views.switch, name='switch'),
    # 开关自动
    path('add/', views.add, name='add'),
    # 添加服务器
    path('add_judge/', views.add_judge, name='add_judge'),
    # 添加服务器信息判断
    path('add_deal/', views.add_deal, name='add_deal'),
    # 添加服务器验证
    path('server_change/', views.server_change, name='server_change'),
    # 修改服务器信息
    path('server_change_deal/', views.server_change_deal, name='server_change_deal'),
    # 修改服务器信息验证
    path('delete/', views.delete, name='delete'),
    # 删除服务器
    path('show/', views.show, name='show'),
    # 服务器概况
    path('control/', views.control, name='control'),
    # 服务器操作
    path('connect_test/', views.connect_test, name='connect_test'),
    # 服务器连接情况测试
    path('record/', views.record, name='record'),
    # 单个服务器登录记录信息
    path('view/', views.view, name='view'),
    # 单个服务器详细信息
    path('view_geo/', views.view_geo, name='view_geo'),
    # 单个服务器地理图展示
    path('log/', views.log, name='log'),
    # 单个服务器日志信息
    path('today_ban/', views.today_ban, name='today_ban'),
    # 单个服务器当日异常处理信息
    path('log_ban/', views.log_ban, name='log_ban'),
    # 单个服务器日志信息
    path('log_add/', views.log_add, name='log_add'),
    # 单个服务器更新100条新数据
    path('log_command/', views.log_command, name='log_command'),
    # 单个服务器封禁IP命令操作
    path('command/', views.command, name='command'),
    # 单个服务器命令行操作界面
    path('command_judge/', views.command_judge, name='command_judge'),
    # 单个服务器判断连接是否成功
    path('command_deal/', views.command_deal, name='command_deal'),
    # 单个服务器命令行接收名执行命令界面
    path('download/', views.download, name='download'),
    # 分析结果数据下载
    path('test/', views.test, name='test'),
    # 测试用
]

