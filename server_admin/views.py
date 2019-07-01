from django.shortcuts import render, HttpResponse, redirect
from django.http import FileResponse
# 下载文件使用
from django.utils.http import urlquote
# 解决下载文件中文名出错
from .models import userInfo, serverInfo
import os, sys, time, re
import json, hashlib
import paramiko
# 远程连接
import threading, multiprocessing
from datetime import datetime

di_command = {}
# 多线程判断命令行是否连接成功以及发送命令用
# 格式：{admin: {"server_name":xxx, "connect_status":0/1/-1, "connect": conn}, ...}
# 装饰器判断页面是否为command，否则清空该用户信息
di_record = {}
# 保存登录记录信息
# 格式：{admin: {"server_name":[20, li_record]}}
# (20, li_record)：下标从0开始第几条数据
# 装饰器判断页面是否为record，否则清空该用户信息
di_safe = {}
# 保存日志信息
# 格式：{admin: {"server_name":[20, li_safe]}}
# (20, li_safe)：下标从0开始第几条数据
# 装饰器判断页面是否为log，否则清空该用户信息
di_ban = {}
# 保存封禁IP信息
# 格式：{admin: {"server_name":[20, li_ban]}}
# 装饰器判断页面是否为log_ban，否则清空该用户信息
di_today_ban = {}
# 保存当日异常处理信息
# 格式：{admin: {"server_name":[20, li_today_ban]}}
# 装饰器判断页面是否为today_ban，否则清空该用户信息

def judgeCookie(request):
# 检查是否cookie验证通过，否则跳转登录页面，并发送msg请先登录
# 完成
	result = {}
	di = {}
	
	try:
		# print(request.META.get('REMOTE_ADDR'))
		name = json.loads(request.COOKIES.get("name"))
		password = json.loads(request.COOKIES.get("verify"))
		result["nav_control"] = 1
		if name:
			user = userInfo.objects.filter(user_name=name).first()
			if user:
				di_user = eval(str(user))
				user_id, user_pwd, user_email, user_company, user_date = di_user['user_id'], di_user['user_pwd'], di_user['user_email'], di_user['user_company'], di_user['user_date']
				if str(hashlib.md5(bytes(user_pwd + '.log', encoding='utf-8')).hexdigest()) == password:
					# cookie验证通过
					server = serverInfo.objects.filter(server_admin=user_id).all()
					for each in server:
						each = eval(str(each))
						server_name = each.pop("server_name")
						di[server_name] = each

					user.user_server_num = len(di)
					user.save()
					# 修改用户所拥有服务器数量

					# 用户基本信息
					result["email"] = user_email
					result["company"] = user_company
					result["date"] = user_date

					# 用户所有服务器信息
					result["server"] = di
					result["server_num"] = len(di)
					result["name"] = name
					result["status"] = 1

				else:
					result["status"] = 0
			else:
				result["status"] = 0
		else:
			result["status"] = -1

		return result

	except Exception as e:
		print("judgeCookie", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_wrapper_log", "a", encoding="utf-8"))
		#没有cookie信息
		result["msg"] = "请先登录"
		result["status"] = -1
		return result


def judgeHook(func):
# 装饰器，类似钩子函数，在进入每个路由前都对是否登录进行检查
# 完成
	def wrapper(request):
		result = {}
		try:
			result = judgeCookie(request)
			# print(json.dumps(result))
			if result.get("name", None):
				# 登录状态下判断访问路由，清空无用数据
				if request.path != '/admin/download/':
					if request.path != '/admin/log_command/' and request.path != '/admin/log_add/':
					# 访问页面非log_command时判断是否为其他log页面
						if request.path != '/admin/log_ban/':
						# 访问页面非log_ban时清空该用户数据
							if di_ban.get(result["name"], None):
								di_ban.pop(result["name"], None)
						if request.path != '/admin/log/':
						# 访问页面非log时清空该用户数据
							if di_ban.get(result["name"], None):
								di_safe.pop(result["name"], None)
						if request.path != '/admin/today_ban/':
						# 访问页面非today_ban时清空该用户数据
							if di_today_ban.get(result["name"], None):
								di_today_ban.pop(result["name"], None)
					if request.path != '/admin/command_deal/' and request.path != '/admin/command_judge/' and request.path != '/admin/command/':
					# 访问页面非command_deal、command_judge和command中的任意一个时，清空该用户数据
						if di_command.get(result["name"], None):
							try:
								di_command[result["name"]]["connect"].close()
								# 先关闭连接
							except Exception as e:
								pass
							di_command.pop(result["name"], None)

			if result["status"] == -1:
				# 无cookie
				return render(request, "login.html", result)
			elif result["status"] == 0:
				# cookie信息错误
				response = redirect('/login')
				response.delete_cookie("name")
				response.delete_cookie("verify")
				return response
			elif result["status"] == 1:
				# cookie认证成功
				return func(request, result)
			else:
				raise Exception("服务器繁忙")

		except Exception as e:
			print("judgeHook", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_wrapper_log", "a", encoding="utf-8"))
			result['msg'] = "服务器繁忙"
			return render(request, "404.html", result, status=404)
	return wrapper


# Create your views here.
@judgeHook
def admin(request, result):
# 管理员信息主页
# 包括用户名、邮箱、公司、注册时间
# 跳转编辑信息页面
# 完成
	if request.method == 'GET':
		return render(request, "admin.html", result)
	else:
		result['msg'] = 'The index page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def change(request, result):
# 修改用户信息，包括：
# 旧密码、新密码、再次新密码、邮箱、所属机构
# 完成
	if request.method == 'GET':
		return render(request, "admin_change.html", result)
	else:
		result['msg'] = 'The change page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def change_deal(request, result):
# 修改用户信息逻辑
# 旧密码不为空则判断新密码
# 邮箱、所属机构修改
# 完成
	if request.method == 'POST':
		try:
			name = result['name']
			old_password = request.POST['old_password']
			password = request.POST['password']
			password2 = request.POST['password2']
			email = request.POST['email']
			company = request.POST['company']
			user = userInfo.objects.filter(user_name=name).first()
			if old_password != '':
				if old_password == user.user_pwd:
					if password != password2:
						raise Exception("两次密码输入不一致")
					else:
						user.user_pwd = password
				else:
					raise Exception("原密码验证错误")
			
			if email != '' and company != '':
				if re.match(r'^[0-9a-zA-Z_]{0,19}@[0-9a-zA-Z]{1,13}\.[com,cn,net]{1,3}$', email):
					user.user_email = email
					user.user_company = company
					user.save()
				else:
					raise Exception("邮箱格式有误")
			else:
				raise Exception("修改数据请勿为空")

			return redirect('/admin/')

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/change_deal", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The change_deal page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def switch(request, result):
# 开启/关闭自动获取数据
# 完成
	if request.method == 'POST':
		try:
			name = result["name"]
			server_name = request.POST["server_name"]
			if name:
				user = userInfo.objects.filter(user_name=name).first()
				if user:
					user_id = eval(str(user))["user_id"]
					server = serverInfo.objects.filter(server_admin=user_id, server_name=server_name).first()
					if server:
						if server.server_auto == 0 and server.server_status == 1:
							server.server_auto = 1
						else:
							server.server_auto = 0
						server.save()
						result_switch = {"switch": server.server_auto}
					return HttpResponse(json.dumps(result_switch))

		except Exception as e:
			return HttpResponse("wrong")
	else:
		result['msg'] = 'The switch page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def add(request, result):
# 添加用户服务器，包括：
# 服务器名、IP、用户名、密码、系统（centos、ubuntu等等，还有其他）
# （可选，用于/admin/connect接口自动获取）
# 完成
	if request.method == 'GET':
		return render(request, "admin_add.html", result)
	else:
		result['msg'] = 'The add page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


def add_judge(request):
# 返回服务器名判断结果
# 完成
	result = {}
	if request.method == 'POST':
		try:
			request_value = request.POST['value']
			request_type = request.POST['type']
			request_user = request.POST['user']
			if request_type == "name":
				user = userInfo.objects.filter(user_name=request_user).first()
				if user:
					user_id = eval(str(user))['user_id']
					server = serverInfo.objects.filter(server_name=request_value, server_admin=user_id).first()
					# print(server, user_id, request_value)
					result["type"] = "name"
					if server:
						result["status"] = 0
					else:
						result["status"] = 1
				return HttpResponse(json.dumps(result))
		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/add_judge", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The add_judge page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def add_deal(request, result):
# 处理添加服务器逻辑，其中ip需要正则判断
# 判断数据是否有空
# 完成
# 可以加个密码数据库加密，取出时反解密
# 加密方式（添加服务器时加密存储）：
# b = a[0]
# a = a[1:]
# c = b + a[::-1][len(a)//3:len(a)//2] + "/" + a[::-1][:len(a)//3] + "/" + a[::-1].swapcase()[len(a)//2:]
# 解密（在models中解密返回）：
# d = c[0]
# c = c[1:].split('/')
# e = d + (c[1] + c[0] + c[2].swapcase())[::-1]
	if request.method == 'POST':
		try:
			server_admin = request.POST['admin']
			server_name = request.POST['name']
			server_ip = request.POST['ip']
			server_user = request.POST['user']
			server_pwd = request.POST['password']
			server_pwd2 = request.POST['password2']
			server_os = request.POST['os']
			try:
				server_port = request.POST.get('port', "")
				if server_port != '':
					server_port = int(server_port)
				else:
					server_port = 22
			except Exception as e:
				print(e)
				result["msg"] = '请输入正确的端口号'
				raise Exception('请输入正确的端口号')
			if server_pwd != server_pwd2:
				result["msg"] = '两次密码输入不一致'
				raise Exception('两次密码输入不一致')
			if server_admin == '' or server_name == '' or server_ip == '' or server_user == '' or server_pwd == '' or server_os == '':
				result["msg"] = '数据请勿为空'
				raise Exception('数据请勿为空')
			if not re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", server_ip):
				result["msg"] = '请输入正确的ip地址'
				raise Exception('请输入正确的ip地址')

			user = userInfo.objects.filter(user_name=server_admin).first()
			if user:
				user_id = int(eval(str(user))['user_id'])

				# 服务器密码加密
				tmp = server_pwd[0]
				server_pwd = server_pwd[1:]
				server_pwd_secret = tmp + server_pwd[::-1][len(server_pwd)//3:len(server_pwd)//2] + "/" + server_pwd[::-1][:len(server_pwd)//3] + "/" + server_pwd[::-1].swapcase()[len(server_pwd)//2:]

			server = serverInfo.objects.create(server_admin_id=user_id, server_name=server_name, server_ip=server_ip, server_port=server_port, server_user=server_user, server_pwd=server_pwd_secret, server_os=server_os)
			# create的时候外键要加上"_id"，应该是原生问题，其他版本可能会有改进

			log_position = "../log_backup/" + str(server_admin) + "/" + str(server_name)
			# 初始化文件夹
			try:
				os.makedirs(log_position)
			except Exception as e:
				pass

			# 初始化文件
			try:
				li_init_file = ["/log", "/safe", "/ban", "/record.csv", "/result.csv", "/abnormal.csv", "/ban.csv", "/today_ban.csv", "/visual_geo.csv", "/visual_bar.js", "/visual_line.js"]
				for each in li_init_file:
					with open(log_position + each, "w", encoding="utf-8") as f:
						pass
			except Exception as e:
				print(e)

			result["status"] = "添加服务器成功"
			result["code"] = 1
			return render(request, "admin_add_result.html", result)

		except Exception as e:
			print("admin/add_deal", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			result["status"] = "添加服务器失败"
			result["code"] = 0
			return render(request, "admin_add_result.html", result)
	else:
		result['msg'] = 'The add_deal page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def server_change(request, result):
# 修改服务器信息，包括：
# IP地址、端口号、用户名、密码
# 完成
	if request.method == 'GET':
		server_name = request.GET['server_name']
		server_ip = result['server'][server_name]['server_ip']
		server_port = result['server'][server_name]['server_port']
		server_user = result['server'][server_name]['server_user']
		result['server_name'] = server_name
		result['ip'] = server_ip
		result['port'] = server_port
		result['user'] = server_user
		return render(request, "admin_server_change.html", result)
	else:
		result['msg'] = 'The server_change page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def server_change_deal(request, result):
# 修改服务器信息逻辑
# 旧密码不为空则判断新密码、正则判断IP地址、端口号范围、用户名
# 完成
	if request.method == 'POST':
		try:
			name = result['name']
			server_name = request.POST["server_name"]
			# 判断ip
			server_ip = request.POST['ip']
			if not re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", server_ip):
				result["msg"] = '请输入正确的ip地址'
				raise Exception('请输入正确的ip地址')
			# 判断端口
			try:
				server_port = int(request.POST['port'])
				if 0 <= server_port <= 65535:
					pass
				else:
					result["msg"] = '请输入正确的端口号'
					raise Exception("请输入正确的端口号")
			except Exception as e:
				result["msg"] = '请输入正确的端口号'
				raise  Exception("请输入正确的端口号")

			server_user = request.POST['user']

			# 判断两次输入密码
			server_pwd = request.POST['password']
			server_pwd2 = request.POST['password2']
			if server_pwd != server_pwd2:
				raise Exception("两次密码输入不一致")

			# 修改数据
			user = userInfo.objects.filter(user_name=name).first()
			if user:
				server = serverInfo.objects.filter(server_name=server_name).first()
				if server:
					tmp = server_pwd[0]
					server_pwd = server_pwd[1:]
					server_pwd_secret = tmp + server_pwd[::-1][len(server_pwd)//3:len(server_pwd)//2] + "/" + server_pwd[::-1][:len(server_pwd)//3] + "/" + server_pwd[::-1].swapcase()[len(server_pwd)//2:]

					# IP地址、端口号、用户名、密码
					server.server_ip = server_ip
					server.server_port = server_port
					server.server_user = server_user
					server.server_pwd = server_pwd_secret
					server.save()

					result["status"] = "修改服务器信息成功"
					result["code"] = 1
					return render(request, "admin_server_change_result.html", result)

				else:
					raise Exception("服务器信息错误！")
			else:
				raise Exception("用户信息错误！")

		except Exception as e:
			print("admin/server_change_deal", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			result["status"] = "修改服务器信息失败"
			result["code"] = 0
			result['server_name'] = server_name
			return render(request, "admin_server_change_result.html", result)

	else:
		result['msg'] = 'The server_change_deal page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def delete(request, result):
# 删除用户服务器，包括：
# 用户名、服务器名
# 完成
	if request.method == 'GET':
		try:
			name = result["name"]
			server_name = request.GET["server_name"]
			user = userInfo.objects.filter(user_name=name).first()
			if user:
				user_id = user.user_id
				server = serverInfo.objects.filter(server_name=server_name, server_admin=user_id)
				if server:
					server.delete()
					del_all('../log_backup/' + name + '/' + server_name)
				else:
					raise Exception("服务器不存在")
			else:
				raise Exception("用户不存在")

			return redirect('/admin/control')

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/delete", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The delete page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


def del_all(root_path):
# 删除服务器同时清空该服务器目录及内容
# 完成
	try:
		dirs = os.listdir(root_path)
		for each in dirs:
			judge_path = root_path + "/" + each;
			if os.path.isdir(judge_path):
				del_all(judge_path)
			elif os.path.isfile(judge_path):
				os.remove(judge_path)
		os.rmdir(root_path)

	except Exception as e:
		print("admin/delete", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))


@judgeHook
def show(request, result):
# 服务器参数设置，大致参数，安全情况，管理等
# 详细信息页面跳转、服务器添加跳转
# 基本完成
	if request.method == 'GET':
		return render(request, "admin_show.html", result)
	else:
		result['msg'] = 'The show page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def control(request, result):
# 用户所有服务器详细情况即控制界面（包括：
# 基本信息展示：服务器、IP地址、用户名、系统类型、启动状态、自动获取数据、启用时间、
# 最近更新时间、是否存在异常情况（跳转查看异常记录-log）、已初始化日志信息（跳转分析结果-view）、进入命令控制台（command）
# 基本完成
	if request.method == 'GET':
		return render(request, "admin_control.html", result)
	else:
		result['msg'] = 'The control page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def connect_test(request, result):
# 测试能否连通服务器
# 完成
	if request.method == 'POST':
		try:
			name = result['name']
			server_name = request.POST['server_name']

			for each in result["server"]:
				if each == server_name:
					server_id = result["server"][each]["server_id"]
					server_ip = result["server"][each]["server_ip"]
					server_user = result["server"][each]["server_user"]
					server_pwd = result["server"][each]["server_pwd"]
					server_port = result["server"][each]["server_port"]
					break

			# 连接服务器
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			server = serverInfo.objects.filter(server_id=server_id).first()
			try:
				ssh.connect(hostname=server_ip, port=server_port, username=server_user, password=server_pwd)
				# 连接失败将服务器连接情况设置为0
				server.server_status = 1
				server.save()
			except Exception as e:
				# 连接失败将服务器连接情况设置为0，并关闭自动更新
				server.server_status = 0
				server.server_auto = 0
				server.save()
				return HttpResponse(json.dumps({"status": 0}))
				# 1-可连接，0-不可连接，-1-未知错误

			ssh.close()
			return HttpResponse(json.dumps({"status": 1}))

		except Exception as e:
			print("admin/connect_test", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return HttpResponse(json.dumps({"status": -1}))

	else:
		result['msg'] = 'The connect_test page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def view(request, result):
# 服务器详细数据统计分析结果
# 日登陆次数、日使用时间、登录地区分布
# 完成
	if request.method == 'GET':
		try:
			server_name = request.GET["server_name"]
			name = result["name"]
			result["server_name"] = server_name
			result["content"] = {}
			# print(result)
			result["server"] = result["server"][server_name]
			with open("../log_backup/" + name + "/" + server_name + "/visual_bar.js", "r", encoding="utf-8") as f:
				content_bar = f.read()
				result["content"]["bar"] = content_bar, len(content_bar)
			with open("../log_backup/" + name + "/" + server_name + "/visual_line.js", "r", encoding="utf-8") as f:
				content_line = f.read()
				result["content"]["line"] = content_line, len(content_line)
			return render(request, "admin_view.html", result)

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/view", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The view page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def view_geo(request, result):
# 服务器地理图信息展示
# 完成
	if request.method == 'GET':
		try:
			server_name = request.GET["server_name"]
			result["server_name"] = server_name
			result["nav_control"] = 0
			return render(request, "admin_geo.html", result)

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/view_geo", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The view_geo page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def record(request, result):
# 登录记录，读取管理员/服务器名/record.csv
# 包括日期、登录时间、登出时间、总用时、用户名、IP、端口、登录类型（密码/密钥）
# 完成
	li_record = []
	# 登录记录

	if request.method == 'GET':
		try:
			name = result["name"]
			server_name = request.GET["server_name"]
			result["server_name"] = server_name

			# 读取封禁IP
			with open("../log_backup/" + name + "/" + server_name + "/record.csv", "r", encoding="utf-8", errors="ignore") as f:
				f.readline()
				li_record_content = f.read().split('\n')
				for each in li_record_content:
					if each == '':
						pass
					else:
						li_record.append(each.split(','))

			# print(li_record[:20])

			result['record'] = li_record[:20]
			di_record[name] = [20, li_record[20:]]
			# 先获取20条，以后进行ajax更新
			while "" in li_record:
				li_record.remove("")
			if len(li_record) == 0:
				result['record_len'] = 0
			return render(request, "admin_record.html", result)

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/record", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The record page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


def log_abnormal_thread(log_position=""):
# 读取异常记录，并生成abnormal.csv文件
# 完成
	li_ban = []
	li_safe = []
	# 读取封禁IP
	with open(log_position + "ban", "r", encoding="utf-8", errors="ignore") as f:
		li_ban_content = f.read().split('\n')
		for each in li_ban_content:
			if each == '' or each[0] == '#':
				pass
			else:
				li_ban.append(each.split(':')[1].strip())

	# 读取暴力破解IP
	with open(log_position + "safe", "r", encoding="utf-8", errors="ignore") as f:
		li_safe_content = f.read().split('\n')
	for each in li_safe_content:
		if each == '':
			pass
		else:
			try:
				date_ip, times = each.split(' = ')
				# print(date_ip)
				date, ip = date_ip.split(':')
				# 详细记录
				if ip in li_ban:
					li_safe.append((date, ip, times, 1))
				else:
					li_safe.append((date, ip, times, 0))
			except Exception as e:
				pass

	# 异常记录保存至本地
	with open(log_position + "abnormal.csv", "w", encoding="utf-8") as f:
		f.write("date,ip,times,ban\n")
		for each in li_safe:
			f.write(each[0] + "," + each[1] + "," + each[2] + "," + str(each[3]) + "\n")


def log_ban_thread(log_position=""):
# 读取封禁记录，并生成ban.csv文件
# 完成
	li_ban = []
	with open(log_position + "ban", "r", encoding="utf-8", errors="ignore") as f:
		li_ban_content = f.read().split('\n')
	for each in li_ban_content:
		if each == '' or each[0] == '#':
				pass
		else:
			li_ban.append(each.split(':')[1].strip())

	# 封禁记录保存至本地
	with open(log_position + "ban.csv", "w", encoding="utf-8") as f:
		f.write("ip\n")
		for each in li_ban:
			f.write(each + "\n")


@judgeHook
def log(request, result):
# 异常记录结果，即读取abnormal.csv文件内容并展示
# 完成
	li_safe = []
	# 暴力破解名单

	if request.method == 'GET':
		try:
			name = result["name"]
			server_name = request.GET["server_name"]
			result["server_name"] = server_name
			file_dir = "../log_backup/" + name + "/" + server_name
			# 读取异常记录
			with open(file_dir + "/abnormal.csv", "r", encoding="utf-8", errors="ignore") as f:
				f.readline()
				li_safe_content = f.read().split('\n')
				while "" in li_safe_content:
					li_safe_content.remove("")
				if len(li_safe_content) > 0:
					for each in li_safe_content:
						if each == "":
							continue
						each = each.split(',')
						li_safe.append((each[0], each[1], each[2], each[3]))

					result['safe'] = li_safe[:20]
					di_safe[name] = [20, li_safe[20:]]
					# 先获取20条，以后进行ajax更新
				else:
					result['safe_len'] = 0
			return render(request, "admin_log.html", result)

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/log", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The log page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def today_ban(request, result):
# 异常记录结果，即读取abnormal.csv文件内容并展示
# 完成
	li_safe = []
	# 暴力破解名单

	if request.method == 'GET':
		try:
			name = result["name"]
			server_name = request.GET["server_name"]
			result["server_name"] = server_name
			file_dir = "../log_backup/" + name + "/" + server_name
			# 读取异常记录
			with open(file_dir + "/today_ban.csv", "r", encoding="utf-8", errors="ignore") as f:
				f.readline()
				li_safe_content = f.read().split('\n')
				while "" in li_safe_content:
					li_safe_content.remove("")
				if len(li_safe_content) > 0:
					for each in li_safe_content:
						if each == "":
							continue
						each = each.split(',')
						li_safe.append((each[0], each[1], each[2]))

					result['today_ban'] = li_safe[:20]
					di_today_ban[name] = [20, li_safe[20:]]
					# 先获取20条，以后进行ajax更新
				else:
					result['today_ban_len'] = 0
			return render(request, "admin_today_ban.html", result)

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/today_ban", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The today_ban page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def log_ban(request, result):
# 显示服务器黑名单
# 提供解封操作
# 完成
	li_ban = []
	# IP封禁名单

	if request.method == 'GET':
		try:
			name = result["name"]
			server_name = request.GET["server_name"]
			result["server_name"] = server_name
			file_dir = "../log_backup/" + name + "/" + server_name
			# 读取封禁IP
			with open(file_dir + "/ban.csv", "r", encoding="utf-8", errors="ignore") as f:
				f.readline()
				li_ban_content = f.read().split('\n')
				if len(li_ban_content) > 0:
					for each in li_ban_content:
						if each == "":
							continue
						li_ban.append((each))

			result['ban'] = li_ban[:20]
			di_ban[name] = [20, li_ban[20:]]
			# 先获取20条，以后进行ajax更新
			while "" in li_ban:
					li_ban.remove("")
			if len(li_ban) == 0:
				result['ban_len'] = 0
			return render(request, "admin_log_ban.html", result)

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/log_ban", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The log_ban page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def log_add(request, result):
# ajax更新20条新数据
# 接收服务器名称和type类型，type=1更新log数据，type=0更新log_ban数据
# 完成
	if request.method == 'POST':
		try:
			name = result["name"]
			server_name = request.POST["server_name"]
			cmd_type = request.POST["type"]

			if cmd_type == '1':
				# 异常记录
				li_return = di_safe[name][1][:20]
				row = di_safe[name][0]
				di_safe[name][1] = di_safe[name][1][20:]
				di_safe[name][0] += 20
			elif cmd_type == '0':
				# 封禁名单
				li_return = di_ban[name][1][:20]
				row = di_ban[name][0]
				di_ban[name][1] = di_ban[name][1][20:]
				di_ban[name][0] += 20
			elif cmd_type == '-1':
				# 登录记录
				li_return = di_record[name][1][:20]
				row = di_record[name][0]
				di_record[name][1] = di_record[name][1][20:]
				di_record[name][0] += 20
			
			return HttpResponse(json.dumps({"status":1, "data": li_return, "row": row}))

		except Exception as e:
			print("admin/log_add", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return HttpResponse(json.dumps({"status": 0}))
	else:
		result['msg'] = 'The log_add page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def log_command(request, result):
# 接收封禁/解封IP等命令并进行处理
# 强制踢出用户、锁定用户可做可不做
# 完成
	if request.method == 'POST':
		try:
			name = result['name']
			server_name = request.POST['server_name']
			log_position = "../log_backup/" + name + "/" + server_name + "/"
			cmd_type = request.POST.get('type', '1')
			ip = request.POST['ip']

			for each in result["server"]:
				if each == server_name:
					server_ip = result["server"][each]["server_ip"]
					server_user = result["server"][each]["server_user"]
					server_pwd = result["server"][each]["server_pwd"]
					server_port = result["server"][each]["server_port"]
					break

			# 连接服务器
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			try:
				ssh.connect(hostname=server_ip, port=server_port, username=server_user, password=server_pwd)
			except Exception as e:
				# 连接失败将服务器连接情况设置为0
				servers = serverInfo.objects.filter(server_ip=server_ip, server_user=server_user, server_pwd=server_pwd, server_port=server_port).all()
				for server in servers:
					server.server_status = 0
					server.save()

				return HttpResponse(json.dumps({"ip_status": 0}))

			# 封禁IP
			if cmd_type == '0':
				cmd = 'echo "sshd: %s : deny" >> /etc/hosts.deny' % ip
			# 解封IP
			elif cmd_type == '1':
				cmd = "sed 's/sshd: %s : deny//g' /etc/hosts.deny > tmp; cat tmp > /etc/hosts.deny" % ip
			else:
				return HttpResponse(json.dumps({"ip_status": 0}))

			stdin, stdout, stderr = ssh.exec_command(cmd)
			result_out = stdout.read().decode()

			stdin, stdout, stderr = ssh.exec_command("cat /etc/hosts.deny")
			# 删除空行：awk NF /etc/hosts.deny > tmp; cat tmp > /etc/hosts.deny
			with open(log_position + "ban", "w", encoding="utf-8", errors="ignore") as f:
				f.write(stdout.read().decode("utf-8"))

			ssh.close()

			# 更新异常和封禁名单
			log_abnormal_thread(log_position)
			log_ban_thread(log_position)

			return HttpResponse(json.dumps({"ip_status": 1}))

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/log_command", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)

	else:
		result['msg'] = 'The log page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def command(request, result):
# 进入命令控制台，开启服务器后台连接进程
# 完成
	if request.method == 'GET':
		try:
			server_name = request.GET["server_name"]
			cmd_type = request.GET["cmd_type"]
			name = result["name"]
			result["server_name"] = server_name
			result["cmd_type"] = cmd_type
			for each in result["server"]:
				if each == server_name:
					server_ip = result["server"][each]["server_ip"]
					server_user = result["server"][each]["server_user"]
					server_pwd = result["server"][each]["server_pwd"]
					server_port = result["server"][each]["server_port"]
					result["server_port"] = server_port
					result["server_user"] = server_user
					break
				else:
					continue
				raise Exception("服务器不存在！")
			di_command[name] = {"server_name":server_name, "connect_status": 0}
			# 0-连接中， 1-连接成功， -1-连接失败
			t = threading.Thread(target=command_thread, args=(name, server_name, server_ip, server_port, server_user, server_pwd, result))
			t.start()
			# print(result)
			return render(request, "admin_command.html", result)

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/command", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The command page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


def command_thread(name, server_name, ip, port, user, password, result):
# 后台进程连接服务器
# 完成
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		ssh.connect(hostname=ip, port=port, username=user, password=password)
		di_command[name]["connect_status"] = 1
		
		if result["cmd_type"] == "invoke":
			channel = ssh.invoke_shell()
			di_command[name]["connect"] = channel
		elif result["cmd_type"] == "single":
			di_command[name]["connect"] = ssh
		else:
			raise Exception("命令行模式有误！")

	except Exception as e:
		# 连接失败将服务器连接情况设置为0
		print("admin/command_thread:用户-%s的服务器-%s连接失败" % (name, server_name), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_thread_log", "a", encoding="utf-8"))
		user = userInfo.objects.filter(user_name=name).first()
		if user:
			admin = user.user_id
			server = serverInfo.objects.filter(server_admin=admin, server_name=server_name).first()
			if server:
				server.server_status = 0
				server.save()
		di_command[name]["connect_status"] = -1


@judgeHook
def command_judge(request, result):
# 判断服务器连接是否成功
# 完成
	if request.method == 'POST':
		try:
			name = result["name"]
			# print(di_command)
			server = di_command[name]
			
			if server["server_name"] == request.POST["server_name"]:
				server_return = {"server_name": server["server_name"], "connect_status": server["connect_status"]}
				return HttpResponse(json.dumps(server_return))
			else:
				return HttpResponse("wrong")

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/command_judge", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The command_judge page cannot visit by get method.'
		return render(request, "404.html", result, status=404)		


@judgeHook
def command_deal(request, result):
# 通过ajax发送命令，对其执行和返回执行结果
# 完成
	if request.method == 'POST':
		try:
			cmd = request.POST["command"]
			cmd_type = request.POST["cmd_type"]
			name = result["name"]
			server = di_command[name]
			ssh = server["connect"]
			if cmd == "-1":
				ssh.close()
				di_command.pop(name)
				return HttpResponse(json.dumps({"msg": "已关闭连接"}))
			else:
				if cmd_type == "single":
					stdin, stdout, stderr = ssh.exec_command(cmd)
					result_out = stdout.read().decode()
					result_err = stderr.read().decode()
					if result_out:
						return HttpResponse(json.dumps({"msg": str(result_out)}))
					elif result_err:
						return HttpResponse(json.dumps({"msg": str(result_err)}))
				elif cmd_type == "invoke":
					ssh.send(cmd + "\n")
					time.sleep(0.5)
					buf = ssh.recv(2024).decode("utf-8")
					return HttpResponse(json.dumps({"msg": str(buf)}))
				else:
					raise Exception("命令行模式有误！")

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/command_deal", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)

	else:
		result['msg'] = 'The command_deal page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def download(request, result):
# 将数据统计结果下载到本地
# 包括登录记录(record.csv)、日登陆时间(result.csv)、登录地区情况(visual_geo.csv)的下载
# 完成
	if request.method == 'GET':
		try:
			name = result["name"]
			server_name = request.GET['server_name']
			file_name = request.GET['file_name']

			if file_name not in ['record.csv', 'result.csv', 'visual_geo.csv', 'abnormal.csv', 'ban.csv', 'today_ban.csv']:
				raise Exception('下载文件有误！')

			file = open('../log_backup/' + name + '/' + server_name + '/' + file_name, 'rb')  
			response = FileResponse(file)
			response['Content-Type'] = 'application/octet-stream'  
			response['Content-Disposition'] = 'attachment;filename="' + urlquote(name) + '_' + urlquote(server_name) + '_' + file_name + '"'  
			return response

		except Exception as e:
			result['msg'] = '下载文件有误！'
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The download page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def test(request, result):
# 测试用
	if request.method == 'GET':
		return render(request, "admin_test.html", result)
	else:
		result['msg'] = 'The test page cannot visit by post method.'
		return render(request, "404.html", result, status=404)
