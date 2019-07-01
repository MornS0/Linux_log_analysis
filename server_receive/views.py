from django.shortcuts import render, HttpResponse, redirect
from .models import userInfo, serverInfo
import os, os.path, time
from datetime import datetime
import chardet
import re
import random
import json, hashlib
import paramiko
import threading, multiprocessing
from pyecharts import Bar, Line
import requests
import sys
sys.path.append("../")
from server_admin.views import judgeCookie, judgeHook, log_abnormal_thread, log_ban_thread

set_connect = set()
# 多线程自动获取数据用
# 存放自动获取数据的server_id
set_connecting = set()
# 正在进行远程更新的
# 在该集合的server_id都不允许开启新线程更新
di_connect = {}
# 手动更新数据用
# 格式：{admin:{server_name1:0/1/-1, ...}, ...}
# 0/1/-1——更新中/更新成功/更新失败

# 废弃：
# 格式：{admin: {"server_name":xxx, "connect_status":0/1/-1, "connect_result": 0/1}, ...}
# "connect_status":0/1/-1——未连接/连接成功/连接失败
# "connect_result": 0/1——获取数据成功，获取数据失败
di_client = {}
# 接收脚本发送数据用
# 格式：{admin:{server_name1:{1/0}, ...}, ...}
di_country = {}
# 各国经纬度，获取国外IP地理位置用
# 格式：{国家:经纬度}


# Create your views here.
def row_get(request):
# 获取服务器读取多少行数据接口，需要传入用户密钥标识进行认证，
# 用户标识
# 传入文件名和服务器名，必须是已经添加的服务器
# 完成
	result = {'row':'', 'status':0, 'msg': ''}
	if request.method == 'POST':
		try:
			name = request.POST['name']
			pwd = request.POST['pwd']
			server_name = request.POST['server_name']
			user = userInfo.objects.filter(user_name=name).first()
			if user:
				if str(hashlib.md5(bytes(user.user_pwd + '.client', encoding='utf-8')).hexdigest()) == pwd:
					server = serverInfo.objects.filter(server_admin=user.user_id, server_name=server_name).first()
					if server:
						result['row'] = server.server_row
						result['status'] = 1
					else:
						result['msg'] = "服务器不存在"
				else:
					result['msg'] = "密码错误"
			else:
				result['msg'] = "用户名不存在"

			return HttpResponse(json.dumps(result))

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/receive/row_get", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)

	else:
		result['msg'] = 'The row_get page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


def client_get(request):
# 客户端数据上传接口
# 接收客户端发送的数据，一次<=500行，根据上面接口来看获取行数，
# 需要接收用户名、密码、服务器名、上传次数、上传数据、上传行数、剩余数据行数
# 必须是已经添加的服务器
# 完成
	result = {'status':0, 'msg': ''}
	if request.method == 'POST':
		try:
			times = int(request.POST['times'])
			# 第N次发送数据
			name = request.POST['name']
			pwd = request.POST['pwd']
			server_name = request.POST['server_name']
			data = request.POST.getlist('data')
			# 数据内容
			row = int(request.POST['row'])
			# 接收行数
			remain = int(request.POST['remain'])
			# 剩余行数
			file_name = "../log_backup/" + name + "/" + server_name + "/log"
			
			user = userInfo.objects.filter(user_name=name).first()
			if user:
				if str(hashlib.md5(bytes(user.user_pwd + '.client', encoding='utf-8')).hexdigest()) == pwd:
					server = serverInfo.objects.filter(server_admin=user.user_id, server_name=server_name).first()
					if server:
						# if di_client.get(name):
						# 	if di_client.get(server_name):
						if times == 0:
							with open(file_name, "w", encoding="utf-8") as f:
								for each in data:
									f.write(each + '\n')
						else:
							with open(file_name, "a", encoding="utf-8") as f:
								for each in data:
									f.write(each + '\n')

						result['msg'] = '接收成功'
						result['status'] = 1

						server.server_row += row
						server.save()

						if remain == 0:
							# di_client[name].pop(server_name)
							t_client = threading.Thread(target=client_get_thread, args=(file_name, server))
							# 新建一个函数，运行read_content，结束后连接数据库更新时间
							t_client.start()
						# else:
						# 	di_client[name] = {}
						# 	di_client[name][server_name] = 1

					else:
						result['msg'] = "服务器不存在"
				else:
					result['msg'] = "密码错误"
			else:
				result['msg'] = "用户名不存在"

			return HttpResponse(json.dumps(result))

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("admin/receive/client_get", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)

	else:
		result['msg'] = 'The client get page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


def client_get_thread(file_name, server):
# 客户端数据上传线程
# 将接收的数据进行分析，完成后更新服务器最近更新时间
# 完成
	try:
		read_content(file_name)
		server.server_update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		server.save()

	except Exception as e:
		print("server_receive/client_get_thread:", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_thread_log", "a", encoding="utf-8"))


@judgeHook
def geo_get(request, result):
# 获取地理图IP分布
# 完成
	if request.method == 'POST':
		try:
			name = result['name']
			result = {'status':0, 'data': ''}
			server_name = request.POST['server_name']
			with open("../log_backup/" + name + "/" + server_name + "/visual_geo_show.csv", "r", encoding="utf-8") as f:
				result['data'] = f.read()

			return HttpResponse(json.dumps(result))

		except Exception as e:
			print("admin/receive/geo_get", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return HttpResponse(json.dumps(result))

	else:
		result['msg'] = 'The geo_get page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def upload_get(request, result):
# 文件上传接口
# 需要用户名、服务器名验证
# 保存文件：../log_backup/用户名/服务器名/log
# 调用线程分析
# 完成
	if request.method == 'POST':
		try:
			name = result['name']
			server_name = request.POST['server_name']
			content = request.FILES['file'].read()
			
			dir_judge(name, server_name)
			code = chardet.detect(content)['encoding']
			content = content.decode(code)
			row = len(content.split('\n'))
			file_name = "../log_backup/" + name + "/" + server_name + "/log"
			# print(code)
			if code == "ascii":
				with open(file_name, "w", encoding="utf-8") as f:
					f.write(content)
			else:
				with open(file_name, "w", encoding=code) as f:
					f.write(content)

			result["status"] = "上传文件成功"
			result["code"] = 1
			t_upload = threading.Thread(target=upload_thread, args=(name, server_name, file_name, row))
			t_upload.start()
			return render(request, "upload_get_result.html", result)

		except Exception as e:
			print("admin/receive/upload_get", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			result["status"] = "上传文件失败"
			result["code"] = 0			
			return render(request, "upload_get_result.html", result)

	else:
		result['msg'] = 'The upload page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


def upload_thread(admin, server_name, file_name, row):
# 上传日志分析线程
# 直接覆盖了原来的日志文件，因此直接分析整个文件
# 更新数据库最近更新时间、行数
# 完成
	try:
		user = userInfo.objects.filter(user_name=admin).first()
		if user:
			server = serverInfo.objects.filter(server_admin=user.user_id, server_name=server_name).first()
			if server:
				read_content(file_name)
				log_position = os.path.dirname(file_name) + "/"
				# 分析异常记录
				log_abnormal_thread(log_position)
				# 分析封禁记录
				log_ban_thread(log_position)
				server.server_row = row
				server.server_update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				server.save()

	except Exception as e:
		print("server_receive/upload_thread:", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_thread_log", "a", encoding="utf-8"))


@judgeHook
def connect_get(request, result):
# 日志文件手动远程连接更新接口
# 需要用户名、服务器名验证
# 保存文件：../log_backup/用户名/服务器名/log
# 调用线程分析
# 完成
	if request.method == 'POST':
		try:
			name = result['name']
			server_name = request.POST['server_name']

			dir_judge(name, server_name)

			if di_connect.get(name, None):
				# 判断是否已经在更新
				if di_connect[name].get(server_name, None) == 0:
					return HttpResponse(json.dumps({"status": 1}))
				# 没更新则开始更新
			di_connect[name] = {server_name : 0}
			# else:
			# 	di_connect[name] = {server_name}

			t_connect = threading.Thread(target=connect_upgrade_thread, args=(None, name, server_name,))
			t_connect.start()
			return HttpResponse(json.dumps({"status": 1}))
			# 1-更新开始，0-更新出错

		except Exception as e:
			print("admin/receive/connect_get", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))	
			return HttpResponse(json.dumps({"status": 0}))

	else:
		result['msg'] = 'The connect_get page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


@judgeHook
def connect_get_judge(request, result):
# 判断日志文件手动远程更新是否完成
# 需要用户名、服务器名验证
# 完成
	if request.method == 'POST':
		try:
			name = result['name']
			server_name = request.POST['server_name']
			if di_connect[name][server_name] == 0:
						return HttpResponse(json.dumps({"status": 0}))
						# 0-更新中，1-更新完成，-1-更新失败
			elif di_connect[name][server_name] == 1:
				di_connect[name].pop(server_name)
				return HttpResponse(json.dumps({"status": 1}))
			else:
				di_connect[name].pop(server_name)
				return HttpResponse(json.dumps({"status": -1}))

		except Exception as e:
			print("admin/receive/connect_get_judge", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))	
			return HttpResponse(json.dumps({"status": -1}))

	else:
		result['msg'] = 'The connect_get_judge page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


def dir_judge(admin, server_name):
# 判断用户文件目录是否存在
# 目录在./log_backup/user_name/server_name下
# 否则创建该目录
# 完成
	try:
		with open("../log_backup/" + str(admin) + "/" + str(server_name) + "/log", "a", encoding="utf-8") as f:
			pass

	except Exception as e:
		# print(repr(e))
		os.makedirs("../log_backup/" + str(admin) + "/" + str(server_name))
		dir_judge(admin, server_name)


def connect_check_thread():
# 定时检查需要更新服务器线程，默认半小时执行一次
# 服务器定时扫描数据库中status为1的服务器
# 将扫描出的服务器加入到set_connect集合当中待connect_get_thread线程对这些服务器进行数据更新
# 基本完成
	try:
		# while True:
		servers = serverInfo.objects.filter().all()
		for server in servers:
			if server.server_auto == 1:
				set_connect.add(server.server_id)

	except Exception as e:
		print("connect_check_thread", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_thread_log", "a", encoding="utf-8"))


def connect_get_thread():
# 定时取出set_connect中服务器更新数据线程
# 当集合不为空时，弹出其中的服务器id进行获取日志数据并更新
# 启动线程
# 基本完成
	try:
		while len(set_connect) > 0:
			server_id = set_connect.pop()
			if server_id in set_connecting:
				pass
			else:
				t_get = threading.Thread(target=connect_upgrade_thread, args=(server_id,))
				t_get.start()
				# set_connecting.add(server_id)

	except Exception as e:
		print("server_receive/connect_get_thread_thread:", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_thread_log", "a", encoding="utf-8"))


def connect_upgrade_thread(server_id=None, name=None, server_name=None):
# 定时更新服务器数据线程
# 当集合set_connect不为空时，对其中的服务器id进行获取日志数据并更新
# 获取服务器的admin、server_name、server_ip、server_port、server_user、server_pwd、server_row
# 远程连接服务器
# sed命令获取row行数的数据
# a模式追加到日志文件后面
# read_content(file_name)日志分析
# 完成后更新数据库最近更新时间、行数
# 基本完成
	try:
		if name == None or server_name == None:
			server = serverInfo.objects.filter(server_id=server_id).first()
			if server:
				server_admin = server.server_admin
				# 这个是admin表的返回值，一个字典，不是id值，要注意
				server_name = server.server_name
				server_ip = server.server_ip
				server_port = server.server_port
				server_user = server.server_user
				server_row = server.server_row
				server_os = server.server_os
				
				# 服务器密码解密
				server_pwd_secret = server.server_pwd
				tmp = server_pwd_secret[0]
				server_pwd_secret = server_pwd_secret[1:].split('/')
				server_pwd = tmp + (server_pwd_secret[1] + server_pwd_secret[0] + server_pwd_secret[2].swapcase())[::-1]

				user = userInfo.objects.filter(user_id=eval(str(server_admin))["user_id"]).first()
				if user:
					name = user.user_name
				else:
					raise Exception("id为%d的服务器不存在用户" % server_id)
			else:
				raise Exception("不存在id为%d的服务器" % server_id)

		elif server_id == None:
			user = userInfo.objects.filter(user_name=name).first()
			if user:
				user_id = user.user_id
			else:
				raise Exception("不存在name为%s的用户" % name)
			server = serverInfo.objects.filter(server_admin=user_id, server_name=server_name).first()
			if server:
				server_ip = server.server_ip
				server_port = server.server_port
				server_user = server.server_user
				server_row = server.server_row
				server_os = server.server_os
				
				# 服务器密码解密
				server_pwd_secret = server.server_pwd
				tmp = server_pwd_secret[0]
				server_pwd_secret = server_pwd_secret[1:].split('/')
				server_pwd = tmp + (server_pwd_secret[1] + server_pwd_secret[0] + server_pwd_secret[2].swapcase())[::-1]
			else:
				raise Exception("name为%s的用户不存在name为%s的服务器" % (name, server_name))
		else:
			raise Exception("传入数据有误")

		log_position = "../log_backup/" + name + "/" + server_name + "/"
		file_name = "../log_backup/" + name + "/" + server_name + "/log"
		dir_judge(name, server_name)
		
		# 所有Linux日志可能存放目录
		li_os_log = ['/var/log/auth.log', '/var/log/secure']

		# 远程连接获取数据
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		try:
			ssh.connect(hostname=server_ip, port=server_port, username=server_user, password=server_pwd)
			server.server_status = 1
			server.save()
			if server_id:
				set_connecting.add(server_id)

		except Exception as e:
			server.server_status = 0
			server.server_auto = 0
			server.save()
			# 连接失败将服务器连接情况设置为0
			di_connect[name][server_name] = -1
			raise Exception("用户-%s的服务器-%s连接失败" % (name, server_name))

		# 连接成功后的操作

		os_log = None
		# 判断日志文件位置
		for each in li_os_log:
			stdin, stdout, stderr = ssh.exec_command('wc -l ' + each)
			if len(stdout.read()) == 0:
				continue
			else:
				os_log = each
				break

		if not os_log:
			raise Exception("用户-%s的服务器-%s，系统日志不存在" % (name, server_name))

		# 获取IP封禁情况
		stdin, stdout, stderr = ssh.exec_command("cat /etc/hosts.deny")
		with open(log_position + "ban", "w", encoding="utf-8", errors="ignore") as f:
			f.write(stdout.read().decode("utf-8"))
		# 分析封禁记录
		log_ban_thread(log_position)

		# 获取暴力破解情况
		# cat /var/log/auth.log | awk '/Failed/{print $1 $2":"$(NF-3)}' | sort | uniq -c | awk '{print $2" = " $1;}'
		stdin, stdout, stderr = ssh.exec_command("cat " + os_log + " | awk '/Failed/{print $1 $2\":\"$(NF-3)}' | uniq -c | awk '{print $2\" = \"$1;}'")
		content = stdout.read().decode("utf-8")
		
		# 替换月份
		li_month = (('Jan', '01-'), ('Feb', '02-'), ('Mar', '03-'), ('Apr', '04-'), ('May', '05-'), ('Jun', '06-'), ('Jul', '07-'), ('Aug', '08-'), ('Sep', '09-'), ('Oct', '10-'), ('Nov', '11-'), ('Dec', '12-'))
		for each in li_month:
			content = content.replace(each[0], each[1])

		li_content = content.split('\n')

		# 分离时间和内容
		li_dates = []
		li_ips = []
		for each in li_content:
			if each == '':
				pass
			else:
				li_dates.append(each.split(':')[0])
				li_ips.append(each.split(':')[1])

		# 计算年份
		if li_dates:
		# 存在暴力破解信息
			years = 0
			li_dates.reverse()
			start_month = li_dates[0].split('-')[0]
			for i in range(len(li_dates)):
				current_time = li_dates[i].split('-')
				current_month = current_time[0]
				if current_month > start_month:
					years += 1
					start_month = current_month
				li_dates[i] = str(datetime.now().year - years)[-2:] + '-' + li_dates[i]
			li_dates.reverse()

		s_safe = ""
		for i in range(len(li_dates)):
			s_safe += li_dates[i] + ":" + li_ips[i] + '\n'
		
		# 记录异常信息
		s_safe = s_safe.split('\n')
		today_ips = create_safe(s_safe, log_position)
		# 分析异常记录
		log_abnormal_thread(log_position)
		# 今日异常处理操作
		auto_ip_ban(log_position, ssh, today_ips)

		# 获取日志文件行数
		stdin, stdout, stderr = ssh.exec_command('wc -l ' + os_log)
		rows = int(stdout.read().decode("utf-8").split(' ')[0])
		get_row = rows - server_row

		# 日志文件异常情况：
		# 数据库记录行数超过日志文件行数
		if get_row < 0:
			os.remove(file_name)
			server.server_row = 0
			server.save()
			get_row = rows
			server_row = 0

		with open(log_position + "log", "r", encoding="utf-8", errors="ignore") as f:
			len_content = len(f.read().split('\n'))
		# 数据库记录行数与本地实际日志文件行数相差超过20
		if abs(len_content - server_row) > 20:
			os.remove(file_name)
			server.server_row = 0
			server.save()
			get_row = rows
			server_row = 0

		# 获取日志文件内容
		while server_row + 10000 < rows:
			stdin, stdout, stderr = ssh.exec_command('sed -n ' + str(server_row+1) + "," + str(server_row+10000) +'p ' + os_log)
			# sed -n x,yp file
			# 查看file文件的x到y行
			content = stdout.read()
			with open(file_name, 'ab') as f:
				f.write(content)
			server_row += 10000
			server.server_row += 10000
			server.save()
			print("文件:" , file_name, "已获取%d行数据" % server_row)

		if rows - server_row <= 10000:
			stdin, stdout, stderr = ssh.exec_command('sed -n ' + str(server_row+1) + "," + str(rows) +'p ' + os_log)
			content = stdout.read()
			with open(file_name, 'ab') as f:
				f.write(content)
			print("文件:" , file_name, "获取数据完成")
		# 断开远程
		ssh.close()

		# 更新读取行数和最近更新时间
		server.server_row = rows
		server.server_update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		server.save()

		# 分析日志开始
		read_content(file_name)

		if server_id == None:
			try:
				di_connect[name][server_name] = 1

			except Exception as e:
				raise Exception("用户-%s，服务器-%s，更新出错" % (name, server_name))
		else:
			try:
				set_connecting.remove(server_id)
			except Exception as e:
				pass

	except Exception as e:
		print("server_receive/connect_upgrade_thread:", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_thread_log", "a", encoding="utf-8"))


def create_safe(content, log_position=""):
# 生成异常记录文件
# 并返回当日的异常情况
# 完成
	di_safe = {}
	# {'date':{'ip':times', 'ip2':times}}
	di_ip_sort = {}
	# {'date':[ip1, ip2, ...], ...}
	# li_day = (('-1:', '-01:'), ('-2:', '-02:'), ('-3:', '-03:'), ('-4:', '-04:'), ('-5:', '-05:'), ('-6:', '-06:'), ('-7:', '-07:'), ('-8:', '-08:'), ('-9:', '-09:'))
	try:
		for each in content:
			if not each:
				continue
			date, ip_time = each.split(':')
			if len(date.split('-')[-1]) < 2:
				date = date[:-1] + '0' + date[-1]
			ip, time = ip_time.split(' = ')
			# print(date, ip, time)
			if date not in di_safe.keys():
				di_safe[date] = {ip:int(time)}
				di_ip_sort[date] = [ip]
			else:
				if ip not in di_safe[date].keys():
					di_safe[date][ip] = int(time)
					di_ip_sort[date].append(ip)
				else:
					di_safe[date][ip] += int(time)

	except Exception as e:
		print("server_receive/connect_upgrade_thread/create_safe:", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_thread_log", "a", encoding="utf-8"))

	li_ip_sort = list(di_ip_sort.keys())
	li_ip_sort.sort()
	# print(li_ip_sort, len(li_ip_sort))
	s_safe = ""
	for each in li_ip_sort:
		for each_ip in di_ip_sort[each]:
			s_safe += each + ":" + each_ip + " = " + str(di_safe[each][each_ip]) + '\n'

	with open(log_position + "safe", "w", encoding="utf-8") as f:
		f.write(s_safe)

	# print(datetime.now().strftime('%Y-%m-%d')[2:])
	return di_safe.get(datetime.now().strftime('%Y-%m-%d')[2:])


def auto_ip_ban(log_position, ssh, today_ips):
# 今日异常处理
# 完成
	try:
		li_ip_ban = []
		# 封禁IP名单
		with open(log_position + "ban.csv", "r", encoding="utf-8", errors="ignore") as f:
			f.readline()
			li_ip_ban = f.read().split('\n')
			while '' in li_ip_ban:
				li_ip_ban.remove('')

		if today_ips:
			s_today_ban = 'date,ip,times\n'
			for ip in today_ips:
				if today_ips[ip] > 5:
					if ip not in li_ip_ban:
						# 不在封禁名单里面则进行封禁
						cmd = 'echo "sshd: %s : deny" >> /etc/hosts.deny' % ip
						stdin, stdout, stderr = ssh.exec_command(cmd)

						# 更新IP封禁名单
						with open(log_position + "ban.csv", "a", encoding="utf-8", errors="ignore") as f:
							f.write('%s\n' % ip)
							
					s_today_ban += datetime.now().strftime('%Y-%m-%d')[2:] + ',' + ip + "," + str(today_ips[ip]) + '\n'

			stdin, stdout, stderr = ssh.exec_command("cat /etc/hosts.deny")
			with open(log_position + "today_ban.csv", "w", encoding="utf-8", errors="ignore") as f:
				f.write(s_today_ban)
			with open(log_position + "ban", "w", encoding="utf-8", errors="ignore") as f:
				f.write(stdout.read().decode("utf-8"))

	except Exception as e:
		print("server_receive/connect_upgrade_thread/auto_ip_ban:", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_thread_log", "a", encoding="utf-8"))


# 如有要过滤分析的IP，如本服务器IP，请加在filter_ip
def read_content(file_name, filter_ip=['127.0.0.1']):
# 读取日志文件，并生成record和result以及可视化文件
# 过滤本地自动连接的IP
# 完成
	li = []
	# 所有数据
	li_result = []
	# 登录记录
	log_type = []
	# 密钥&密码登录
	log_date_times = []
	# 登录日期时间
	log_ips = []
	# 登录IP
	log_ports = []
	# 登录端口
	log_dates = []
	# 登录日期
	log_times = []
	# 登录时间
	log_users = []
	# 登录用户
	log_sshds = []
	# 登录号，匹配登出时间用
	li_month = (('Jan ', '01-'), ('Feb ', '02-'), ('Mar ', '03-'), ('Apr ', '04-'), ('May ', '05-'), ('Jun ', '06-'), ('Jul ', '07-'), ('Aug ', '08-'), ('Sep ', '09-'), ('Oct ', '10-'), ('Nov ', '11-'), ('Dec ', '12-'))
	# 替换日期
	log_position = os.path.dirname(file_name)

	print("reading the file: %s ..." % file_name, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))

	try:
		# 读取日志文件
		with open(file_name , "rb") as f_code:	   
			code = chardet.detect(f_code.readline())['encoding']
		if code == "ascii":
			code = "utf-8"
		with open(file_name, "r", encoding=code, errors='ignore') as f:
			content = str(f.read())
			
	except Exception as e:
		print("read the file : %s wrong!" % file_name, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))
		return

	for each in li_month:
		content = content.replace(each[0], each[1])
		# 月份格式替换成阿拉伯数字

	li = content.split('\n')
	li_close = []
	close_port_format = re.compile('\[(.*?)\]')
	close_time_format = re.compile("\d\d:\d\d:\d\d")
	date_times_format = re.compile(".{0,8}\d\d:\d\d:\d\d")
	ips_format = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
	ports_format = re.compile("port (\d{1,})")
	users_format = re.compile("for (.*?) from")
	sshds_format = re.compile('\[(.*?)\]')

	for each in li:
		# 筛选登录记录
		if "Accepted password" in each:
			if re.findall(ips_format, each)[0] in filter_ip:
				continue
			li_result.append(each)
			log_type.append("password")
			# 密码登录
		if "Accepted publickey" in each:
			if re.findall(ips_format, each)[0] in filter_ip:
				continue
			li_result.append(each)
			log_type.append("publickey")
			# 密钥登录
		if "session closed" in each and "sshd" in each:
			# 登出记录
			close_port = re.findall(close_port_format, each)[0]
			close_user = each.split()[-1]
			close_time = re.findall(close_time_format, each)[0]
			li_close.append((close_port, close_user, close_time))


	for each in li_result:
		log_date_times.append(re.findall(date_times_format, each)[0])
		log_ips.append(re.findall(ips_format, each)[0])
		log_ports.append(re.findall(ports_format, each)[0])
		log_users.append(re.findall(users_format, each)[0])
		log_sshds.append(re.findall(sshds_format, each)[0])

	for each in log_date_times:
		log_dates.append(each[:-9])
		log_times.append(each[-8:])

	if log_dates:
	# 计算年份
		years = 0
		log_dates.reverse()
		start_month = log_dates[0].split('-')[0]
		for i in range(len(log_dates)):
			current_time = log_dates[i].split('-')
			current_month = current_time[0]
			if current_month > start_month:
				years += 1
				start_month = current_month
			log_dates[i] = str(datetime.now().year - years)[-2:] + '-' + log_dates[i]
		log_dates.reverse()
	else:
		print(file_name,":记录为空" , ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))

	print("read the file: %s complete" % file_name, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))

	print("creating the file: %s ..." % str(log_position + "/record.csv"), ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))
	with open(log_position + "/record.csv", "w", encoding="utf-8") as f:
		head = "date,connect time,close time,use time,user,ip,port,longon type\n"
		f.write(head)
		for i in range(len(log_ips)):
			try:
				# 计算单次登录用时
				log_out_time = "24:00:00"
				for j in li_close:
					if j[0] == log_sshds[i]:
						log_out_time = li_close.pop(li_close.index(j))[2]
						break
				
				log_time_i_format = log_times[i].split(':')
				close_time_i_format = log_out_time.split(':')
				log_time_to_second = int(log_time_i_format[0])*3600 + int(log_time_i_format[1])*60 + int(log_time_i_format[2])
				close_time_to_second = int(close_time_i_format[0])*3600 + int(close_time_i_format[1])*60 + int(close_time_i_format[2])
				if log_out_time == "24:00:00":
					use_time_to_second = 24*60*60 - log_time_to_second
				elif close_time_to_second < log_time_to_second:
					use_time_to_second = 24*3600 - log_time_to_second + close_time_to_second
				else:
					use_time_to_second = close_time_to_second - log_time_to_second

				use_time = time_to_format(use_time_to_second)
				contents = "%s,%s,%s,%s,%s,%s,%s,%s\n" % (log_dates[i], log_times[i], log_out_time, use_time, log_users[i], log_ips[i], log_ports[i], log_type[i])

			except Exception as e:
				contents = "%s,%s,-1,-1,%s,%s,%s,%s\n" % (log_dates[i], log_times[i], log_users[i], log_ips[i], log_ports[i], log_type[i])
			finally:
				f.write(contents)

	print("create the file: %s complete" % str(log_position + "/record.csv"), ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))

	print("reading the file: %s ..." % str(log_position + "/result.csv"), ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))
	with open(log_position + "/record.csv", "r", encoding="utf-8") as f:
		f.readline()
		li_contents = f.read().split("\n")
		li_contents_result = []
		i = 0
		for each in li_contents:
			datas = each.split(',')
			if datas[0] == "":
				pass
			elif not li_contents_result:
				li_contents_result.append([datas[0], [datas[1], datas[2], datas[3]] + [1]])
				i += 1
			elif li_contents_result[i-1][0] != datas[0]:
				li_contents_result.append([datas[0], [datas[1], datas[2], datas[3]] + [1]])
				i += 1
			else:
				li_contents_result[i-1][1][-1] += 1
				li_contents_result[i-1][1][1] = datas[2]
				log_time_i_format = li_contents_result[i-1][1][2].split(':')

				close_time_i_format = datas[3].split(':')
				log_time_to_second = int(log_time_i_format[0])*3600 + int(log_time_i_format[1])*60 + int(log_time_i_format[2])
				close_time_to_second = int(close_time_i_format[0])*3600 + int(close_time_i_format[1])*60 + int(close_time_i_format[2])
				use_time_to_second = close_time_to_second + log_time_to_second
				use_time = time_to_format(use_time_to_second)
				li_contents_result[i-1][1][2] = use_time

	with open(log_position + "/result.csv", "w", encoding="utf-8") as f:
			head = "date,log time,logout time,day use time, logon times\n"
			f.write(head)
			li_dates = []
			li_use_times = []
			li_logon_times = []
			
			for each in li_contents_result:
				contents = "%s,%s,%s,%s,%d\n" % (each[0], each[1][0],each[1][1],each[1][2],each[1][3])
				f.write(contents)
				li_dates.append(each[0])

				li_use_time_format = each[1][2].split(':')
				li_use_time_to_second = int(li_use_time_format[0])*3600 + int(li_use_time_format[1])*60 + int(li_use_time_format[2])
				if li_use_time_to_second/3600 > 24:
					li_use_times.append(24)
				else:
					li_use_times.append(li_use_time_to_second/3600)
				li_logon_times.append(each[1][3])

	print("read the file: %s complete" % str(log_position + "/result.csv"), ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))

	# 生成可视化文件
	# 生成bar.js文件
	print("creating the visual file: %s ..." % str(log_position + "/visual_bar.js"), ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))
	bar = Bar("登陆次数/日", "单位:次", width=1200, height=800)
	bar.add("日期", li_dates, li_logon_times,is_more_utils=True)
	config_bar = bar.show_config().replace("True", "true").replace("False", "false").replace("None", "null")
	with open(log_position + "/visual_bar.js", "w", encoding="utf-8") as f:
		content_bar = """var myChart_bar = echarts.init(document.getElementById('bar'));
var option_bar = """ + config_bar + ";\n" + "myChart_bar.setOption(option_bar);"
		f.write(content_bar)	
	print("create the visual file: %s complete" % str(log_position + "/visual_bar.js"), ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))


	# 生成line.js文件
	print("creating the visual file: %s ..." % str(log_position + "/visual.html"), ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))
	line = Line("总用时/日", "单位:小时", width=1200, height=800)
	line.add("日期", li_dates, li_use_times,is_more_utils=True)
	config_line = line.show_config().replace("True", "true").replace("False", "false").replace("None", "null")

	with open(log_position + "/visual_line.js", "w", encoding="utf-8") as f:
		content_line = """var myChart_line = echarts.init(document.getElementById('line'));
var option_line = """ + config_line + ";\n" + "myChart_line.setOption(option_line);"
		f.write(content_line)
	print("create the visual file: %s complete" % str(log_position + "/visual_line.js"), ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))


	# 生成visual_geo.csv/visual_geo_show.csv文件
	print("creating the visual file: %s ..." % str(log_position + "/visual_geo.csv"), ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))

	li_ips = []
	set_ips = set()
	di_ips = {}
	di_locs = {}
	with open(log_position + "/record.csv", "r", encoding="utf-8") as f:
		f.readline()
		for each in f.read().split('\n'):

			each = each.split(',')
			if each == '':
				pass
			elif len(each) == 8:
				li_ips.append(each[-3])

	set_ips = set(li_ips)
	for ip in set_ips:
		di_ips[ip] = li_ips.count(ip)

	init_get_country()
	content_geo = "loc,ip,经纬度,times\n"
	content_geo_show = "loc,ip,经纬度,times\n"

	for ip in di_ips.keys():
		# 先过滤私有IP
		if ip[:7] == "192.168" or ip[:3] == "127":
			continue
		elif ip[:3] == "172":
			ip_each = ip.split('.')
			if 16 <= int(ip_each[1]) <= 31:
				continue
		loc, lng_alt = get_loc(ip)
		if loc == "" or lng_alt == "":
			# 说明为国外地址，通过ip138查
			loc, lng_alt = get_loc_ip138(ip)
		if loc == "" or lng_alt == "":
			# ip138再次查询失败
			continue
		content_geo += loc + "," + ip + "," + lng_alt + "," + str(di_ips[ip]) + "\n"
		if loc not in di_locs:
		# {位置:[[ip1,times],[ip2],times],...], all_times]}
			di_locs[loc] = [lng_alt, [(ip, di_ips[ip])], di_ips[ip]]
		else:
			di_locs[loc][1].append((ip, di_ips[ip]))
			di_locs[loc][2] += di_ips[ip]

	# 地理图数据csv内容格式
	# content_geo = """231,1.1.1.1,"116.397026,39.918058",1
	# 231,1.1.1.1,"106.397026,0.918058",2
	# 231,1.1.1.1,"156.397026,70.918058",3
	# """
	with open(log_position + "/visual_geo.csv", "w", encoding="utf-8") as f:
		f.write(content_geo)

	# 地理图csv内容格式
	# 天津市,（106.47.98.130:9次，180.212.36.188:10次）,"117.21081309,39.14392990",9
	# 地点，ip群（ip:次数，...），经纬度，总次数
	# 源文件不变，再加一个汇总
	for each in di_locs.keys():
		content_geo_show += each + ",（"
		for ip in di_locs[each][1]:
			content_geo_show += ip[0] + " : " + str(ip[1]) + "次，"
		content_geo_show += "）," + di_locs[each][0] + "," + str(di_locs[each][2]) + "\n"

	with open(log_position + "/visual_geo_show.csv", "w", encoding="utf-8") as f:
		f.write(content_geo_show)
		
	print("create the visual file: %s complete" % str(log_position + "/visual_geo.csv"), ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./create_file_log", "a", encoding="utf-8"))


def time_to_format(use_time):
# 格式化时间
	hour = use_time // 3600
	minute = (use_time - hour*3600) // 60
	second = use_time - hour*3600 - minute*60
	use_time_format = "%d:%d:%d" % (hour, minute, second)
	return use_time_format


def get_loc(ip):
# 百度接口获取国内ip的地址信息
	try:
		url = 'http://api.map.baidu.com/location/ip?ip=' + ip + '&ak=' + '输入你的AK' + '&coor=bd09ll'
		header = {
		 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 '
		               '(KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
		}
		res = requests.get(url, headers=header)
		loc_result = json.loads(res.text)
		if loc_result['status'] == 0:
		# 成功获取到地址信息
			lng_alt = '"' + loc_result['content']['point']['x'] + ',' + loc_result['content']['point']['y'] + '"'
			loc = loc_result['content']['address']
			loc2 = loc_result['address']
		# print(lng_alt, loc, loc2)
		# "117.21081309,117.21081309" 天津市 CN|天津|天津|None|CHINANET|0|0
			return loc, lng_alt
		else:
			return "", ""

	except Exception as e:
		print("server_receive/get_loc:", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_api_log", "a", encoding="utf-8"))


def get_loc_ip138(ip):
# ip138接口获取国外ip的信息
# 完成
	try:
		sign = str(hashlib.md5(bytes("ip=" + ip + "&token=" + "输入你的token值", encoding='utf-8')).hexdigest())

		url = "http://api.ip138.com/query/?ip=" + ip + "&callback=find&oid=" + "" + "&mid=" + "" + "&sign=" + sign
		header = {
		 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 '
		               '(KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
		}
		res = requests.get(url, headers=header)
		result = res.text[5:-1]
		loc_result = json.loads(result)
		if loc_result['ret'] == "ok":
			try:
				loc = loc_result['data'][0]
				# 根据地理位置获取坐标
				lng_alt = get_country_lng_alt(loc)
				lng_alt = '"' + lng_alt + '"'
				return loc, lng_alt
			except:
				return "", ""

	except Exception as e:
		print("server_receive/get_loc_ip138:", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_api_log", "a", encoding="utf-8"))

def init_get_country():
# 获取所有国家地理坐标
# 完成
	global di_country
	with open("country_lng_alt", "r", encoding="utf-8") as f:
		country = f.read()
	di_country = eval(country)


def get_country_lng_alt(country="阿富汗"):
# 获取国外IP坐标
# 完成
	if di_country.get(country, None):
		return di_country[country]
	else:
		raise Exception("国家：%s不存在" % country)
