from django.db import models
import sys
sys.path.append("../")
from user_admin.models import userInfo

# 用户目录：../log_backup/server_admin/server_name
# 下面有7个文件：
# log：日志文件
# record：日志记录文件
# result：分析结果文件
# safe：异常信息记录文件
# visual_bar.js：柱形图可视化文件，供html调用
# visual_line.js：折线图可视化文件，供html调用
# visual_geo.js：地理图可视化文件，供html调用


class serverInfo(models.Model):
	server_id = models.AutoField(primary_key=True)
	server_admin = models.ForeignKey(to=userInfo, related_name="server_admin_id", on_delete=models.CASCADE)
	# 用户管理员
	server_name = models.CharField(max_length=45, null=False)
	# 服务器名
	server_ip = models.CharField(max_length=45, null=False)
	# 服务器ip
	server_port = models.IntegerField(default=22, null=False)
	# 服务器端口
	server_user = models.CharField(max_length=45, null=False)
	# 用户名
	server_pwd = models.CharField(max_length=45, null=False)
	# 用户密码
	# server_start_time = models.DateTimeField(null=True)
	# 起始年份
	server_os = models.CharField(max_length=45, null=False)
	# 系统类型
	# server_dir = models.CharField(max_length=45, null=False)
	# # 服务器登录记录文件目录
	server_row = models.IntegerField(default=0, null=False)
	# 服务器读取日志文件行数
	server_status = models.IntegerField(default=0, null=False)
	# 是否启动中
	server_auto = models.IntegerField(default=0, null=False)
	# 是否自动更新
	server_update_time = models.DateTimeField(null=True)
	# 最近更新时间


	class Meta:
		db_table = "server"
		unique_together=("server_admin","server_name")

	def __str__(self):
		self.admin = eval(str(self.server_admin))["user_name"]
		tmp = self.server_pwd[0]
		self.server_pwd = self.server_pwd[1:].split('/')
		e = tmp + (self.server_pwd[1] + self.server_pwd[0] + self.server_pwd[2].swapcase())[::-1]
		return str({
			"server_id":self.server_id,
			"server_admin":self.admin, 
			"server_name":self.server_name, 
			"server_ip":self.server_ip, 
			"server_user":self.server_user, 
			"server_pwd":e, 
			# 解密密码
			# "server_start_time":str(self.server_start_time), 
			# 时间要转换下格式
			"server_os":self.server_os, 
			"server_port":self.server_port, 
			"server_row":self.server_row, 
			"server_status":self.server_status, 
			"server_auto":self.server_auto, 
			"server_update_time":str(self.server_update_time), 
			})