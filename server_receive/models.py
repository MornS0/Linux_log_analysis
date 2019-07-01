from django.db import models
import sys
sys.path.append("../")
from user_admin.models import userInfo
from server_admin.models import serverInfo

# class resultInfo(models.Model):
# 	server_id = models.AutoField(primary_key=True)
# 	# server_admin = models.ForeignKey(to=userInfo, related_name="server_admin_id", on_delete=models.CASCADE)
# 	# 服务器管理员
# 	server_name = models.ForeignKey(to=serverInfo, related_name="server_name_id", on_delete=models.CASCADE)
# 	# 服务器名
# 	server_dir = models.CharField(max_length=45, null=False)
# 	# 服务器登录记录文件目录
# 	server_row = models.IntegerField(default=0)
# 	# 服务器读取日志文件行数
# 	server_update_time = models.DateTimeField(null=True)
# 	# 最近更新时间

# 	class Meta:
# 		db_table = "result"

# 	def __str__(self):
# 		self.admin = eval(str(self.server_name))["server_admin"]
# 		self.name = eval(str(self.server_name))["server_name"]
# 		return str({
# 			"server_admin":self.admin, 
# 			"server_name":self.name, 
# 			"server_dir":self.server_dir, 
# 			"server_row":self.server_row, 
# 			"server_update_time":self.server_update_time, 
# 			})
