import requests
import hashlib
import time
import os

# 步骤：
# 1.第一次发送数据前访问/admin/receive/row接口获取已读行数
# 2.根据已读行数计算传入日志数据行数：os.popen("wc -l /var/log/日志文件").read()-row
# 3.将对应量行数的数据获取到脚本：li = os.popen("tail -行数 /var/log/日志文件").read().split('\n')
# 4.循环发送数据到/admin/receive/client接口，一次默认<=500行数据

li = []
# 存放总共要发送的日志数据
# 一次弹出500条，row=500，remain=len(li)-500，data=li[:500]，li=li[500:]
# 当len(li)<=500时全部发送，row=len(li)，remain=0，data=li，li=0


def post_row(name, pwd, server_name):
# /admin/receive/row_get接口获取已读行数
	url="http://127.0.0.1:6666/admin/receive/row_get/"

	# row接口验证：
	# 用户名
	# 密码（加密）
	# 服务器名
	data_row = {
		"name": name, 
		"pwd": str(hashlib.md5(bytes(pwd + '.client', encoding='utf-8')).hexdigest()), 
		"server_name": server_name, 
	}

	res = requests.post(url, data=data_row)
	# 返回：
	# status——1/0（验证成功/失败）
	# 成功情况下：row——已分析行数，失败情况下：row——""（空）
	# 成功情况下：msg——""，失败情况下：msg——（错误信息）
	# 示例：{"status":1, "row": 500, "msg":""}/{"status":0, "row": "", "msg":"密码错误"}
	di_res = eval(str(res.text))
	return di_res["status"], di_res["row"], di_res["msg"]


def get_data(row, system):
	if system == 2:
		file = "/var/log/auth.log"
	else:
		file = "/var/log/secure"

	try:
		row2 = int(os.popen("wc -l " + file).read().split(' ')[0])
		row_delta = row2 - row

		if row_delta < 0:
			print("数据有误，需初始化日志文件，共%s条..." % row)
			li = os.popen("cat " + file).read().split('\n')
		else:
			print("已更新数据%s条，再需更新%s条..." % (row, row_delta))
			li = os.popen("tail -" + str(row_delta) + " " + file).read().split('\n')
		#if len(li) == row_delta:
		return li, 1
		#return li, 0

	except Exception as e:
		return li, 0
		raise Exception("获取日志数据有误！请检查系统是否选择正确！")


def post_client(name, pwd, server_name, data, row, remain, i):
# 发送数据到/admin/receive/client_get接口，一次默认500行数据
	url="http://127.0.0.1:6666/admin/receive/client_get/"

	# client接口验证：
	# 用户名
	# 密码（加密）
	# 服务器名
	# 日志数据
	# 一次的行数，默认<=500
	# 剩余行数
	# 第i次发送数据

	data_client = {
		"name": name,
		"pwd": str(hashlib.md5(bytes(pwd + '.client', encoding='utf-8')).hexdigest()),
		"server_name": server_name,
		"data": data,
		"row": row,
		"remain": remain,
		"times": i,
	}

	res = requests.post(url, data=data_client)
	# 返回：
	# status——1/0（验证成功/失败）
	di_res = eval(str(res.text))
	return di_res["status"], di_res["msg"]


def main():
	# # 自定义数据
	# name = "11111"
	# pwd = "11111"
	# server_name = "aaa"
	# system = 1
	# status_data = 1
	# with open(r'E:\os\project\log_backup\11111\213\log', 'r', encoding="utf-8", errors="ignore") as f:
	# 	li = f.read().split('\n')
	# # print(len(li))

# 	# 手动输入数据
	try:
		name = input("请输入用户名>>")
		pwd = input("请输入密码>>")
		server_name = input("请输入服务器名>>")

	except Exception as e:
		print("您输入的数据有误，请重新输入")

	try:
		system = int(input("""请选择系统类型：
	1.centos 	2.ubuntu 	3.redhat 	4.debian
（输入系统对应数字代号）>>"""))

	except Exception as e:
		print("您输入的数据有误，请重新输入")


	# 与分析平台交互开始
	try:
		# 获取行数
		status_row, row, msg_row = post_row(name, pwd, server_name)
		# print(status_row, row, msg_row)
	except Exception as e:
		raise Exception("admin/receive/row_get接口连接失败！错误原因：%s" % msg_row)
	
	try:
		if status_row == 1:
			# 获取数据
			li, status_data = get_data(row, system)

			# 发送数据
			if status_data == 1:
				i = 0
				while len(li) > 0:
					if len(li) > 500:
						row = 500
						data = li[:500]
						remain = len(li) - 500
						li = li[500:]
					else:
						row = len(li)
						data = li
						remain = 0
						li = []

					print("第%d次开始发送数据中，发送长度为%d条..." % (i, row))
					status_client, msg_client = post_client(name, pwd, server_name, data, row, remain, i)
					if status_client == 1:
						print("第%d次发送数据成功，剩余发送长度为%d条..." % (i, remain))
						i += 1
					else:
						print("第%d次发送数据失败，错误原因：%s..." % (i, msg_client))
						raise Exception("异常终止！")

				print("用户：%s,服务器：%s,数据上传完成！" % (name, server_name))

					
		else:
			raise Exception("admin/receive/row_get接口信息验证失败！错误原因：%s" % msg_client)

	except Exception as e:
		print(e)


if __name__ == '__main__':
	try:
		main()

	except Exception as e:
		print(e)
		exit()

