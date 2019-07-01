from django.urls import path
from . import views

urlpatterns = [
    # path('', views.index, name='index'),
    path('row_get/', views.row_get, name='row_get'),
    # 获取日志读取行数
    path('geo_get/', views.geo_get, name='geo_get'),
    # 获取地理图IP分布
    path('client_get/', views.client_get, name='client_get'),
    # 客户端脚本发送日志数据
    path('upload_get/', views.upload_get, name='upload_get'),
    # 文件方式上传数据
    path('connect_get/', views.connect_get, name='connect_get'),
    # 日志文件手动远程更新
    path('connect_get_judge/', views.connect_get_judge, name='connect_get_judge'),
    # 日志文件手动远程更新判断
]
