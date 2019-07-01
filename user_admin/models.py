from django.db import models

# Create your models here.

# 用户
class userInfo(models.Model):
	user_id = models.AutoField(primary_key=True)
	user_name = models.CharField(max_length=20, unique=True, null=False)
	# 用户名
	user_pwd = models.CharField(max_length=32, null=False)
	# 密码
	user_email = models.CharField(max_length=45, unique=True, null=False)
	# 邮箱
	user_company = models.CharField(max_length=45, null=False)
	# 公司
	user_server_num = models.IntegerField(default=0)
	# 服务器数量
	user_date = models.DateTimeField(null=False)
	# 注册日期

	class Meta:
		db_table = "admin"

	def __str__(self):
		return str({
			"user_id": self.user_id, 
			"user_name": self.user_name, 
			"user_pwd": self.user_pwd,
			"user_email": self.user_email,
			"user_company": self.user_company,  
			"user_server_num": self.user_server_num,
			"user_date": str(self.user_date),
			})
