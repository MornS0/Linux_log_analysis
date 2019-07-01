from django.shortcuts import render, HttpResponse, redirect
from datetime import datetime
import re
from .models import userInfo
import json, hashlib
import random
from PIL import Image, ImageDraw, ImageFont

# Create your views here.
def get_code(request):
# 更新生成验证码
# 完成
	result = {}
	if request.method == "GET":
		try:
			# new = request.GET.get("new", "")
			# 根据时间生成图片
			code, img_content = create_code()
			request.session["code"] = code
			return HttpResponse(img_content, content_type="image/png")

		except Exception as e:
			print("get_code", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return HttpResponse(json.dumps({"status": 0}))

	else:
		result['msg'] = 'The get_code page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


def create_code():
# 生成验证码
# 完成
	# 定义使用Image类实例化一个长为240px,宽为60px,基于RGB的(255,255,255)颜色的图片
	img1 = Image.new(mode="RGB", size=(240, 60), color=(255, 255, 255))

	# 实例化一支画笔
	draw1 = ImageDraw.Draw(img1, mode="RGB")

	# 定义字体
	font1 = ImageFont.truetype("static/font/mon.ttf", 36)
	# draw.textsize(text,font=None)
	code = ""
	for i in range(4):
	    # 每循环一次,从a到z中随机生成一个字母或数字
	    # 65到90为字母的ASCII码,使用chr把生成的ASCII码转换成字符
	    # str把生成的数字转换成字符串
	    char1 = random.choice([chr(random.randint(65,79)), chr(random.randint(80, 90)), chr(random.randint(97, 111)), chr(random.randint(112, 122)), str(random.randint(1,9))])
	    code += char1
	    # 每循环一次重新生成随机颜色
	    color1 = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
	    
	    # 把生成的字母或数字添加到图片上
	    # 图片长度为240px,要生成4个数字或字母则每添加一个,其位置就要向后移动24px
	    # draw1.text([i*60, 15], char1, fill=color1)
	    draw1.text([i*60, 15], char1, font=font1, fill=color1)

	# 画干扰线
	for i in range(10):
		draw1.line((random.randint(0,240), random.randint(0,60), random.randint(0,240), random.randint(0,60)), fill=(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
		# 10条随机起始位置、颜色的干扰线

	# 把生成的图片保存为"pic.png"格式
	with open("static/img/code.png", "wb") as f:
	    img1.save(f, format="png")

	with open("static/img/code.png", "rb") as f:
		img_content = f.read()
	return code, img_content


def index(request):
# 先检查是否有cookie，如果验证成功，则显示用户名，用户信息、服务器链接，注销
# 没有就显示未登录，然后注册和登录页面跳转
# 界面为中间的框如果登录了就显示信息，否则显示未登录
# 完成
	result = {}
	if request.method == "GET":
		try:
			name = json.loads(request.COOKIES.get("name"))
			password = json.loads(request.COOKIES.get("verify"))
			if name:
				user = userInfo.objects.filter(user_name=name).first()
				if user:
					user_pwd = eval(str(user))['user_pwd']
					if str(hashlib.md5(bytes(user_pwd + '.log', encoding='utf-8')).hexdigest()) == password:
						# cookie验证通过
						# result[]
						result["name"] = name
						result["status"] = 1
						return render(request, "index.html", result)
					else:
						# cookie信息错误，同时删除cookie
						response = redirect('/index')
						response.delete_cookie("name")
						response.delete_cookie("verify")
						return response
			else:
				result["status"] = 0
				return render(request, "index.html", result)

		except Exception as e:
			print("index", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			#没有cookie信息
			result["status"] = 0
			return render(request, "index.html", result)

	else:
		result['msg'] = 'The index page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


def instr(request):
# 使用说明页面
# 完成
	result = {}
	if request.method == 'GET':
		return render(request, "instr.html")
	else:
		result['msg'] = 'The instr page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


def regist(request):
# 注册信息：
# 用户添加：用户名（唯一，ajax判断），密码，邮箱（唯一，ajax判断），企业
# 自动添加：服务器数量默认0，注册日期
# 完成
	result = {}
	if request.method == 'GET':
		return render(request, "regist.html")
	else:
		result['msg'] = 'The regist page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


def regist_deal(request):
# 处理注册逻辑
# 判断密码是否一致，数据是否有空
# 注册成功进入登录界面，失败返回注册页面
# 完成
	result = {}
	if request.method == 'POST':
	# if request.method == 'GET':
		try:
			# 验证码
			# code = request.POST['code']
			# if code.lower() != request.session['code'].lower():
			# 	result["msg"] = '验证码错误'
			# 	raise Exception('验证码错误')
			user_name = request.POST['name']
			user_pwd = request.POST['password']
			user_pwd2 = request.POST['password2']
			user_email = request.POST['email']
			user_company = request.POST['company']
			user_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			if user_pwd != user_pwd2:
				result["msg"] = '两次密码输入不一致'
				raise Exception('两次密码输入不一致')
			if user_name == '' or user_pwd == '' or user_email == '' or user_company == '' or user_date == '' :
				result["msg"] = '数据请勿为空'
				raise Exception('数据请勿为空')
			if not re.match(r'^[0-9a-zA-Z_]{0,19}@[0-9a-zA-Z]{1,13}\.[com,cn,net]{1,3}$', user_email):
				result["msg"] = '邮箱格式有误'
				raise Exception('邮箱格式有误')
				
			user = userInfo.objects.create(user_name=user_name, user_pwd=user_pwd, user_email=user_email, user_company=user_company, user_date=user_date)

			result["status"] = "注册成功"
			result["code"] = 1
			result["name"] = user_name
			return render(request, "regist_result.html", result)

		except Exception as e:
			print("regist_deal", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			result["status"] = "注册失败"
			result["code"] = 0
			return render(request, "regist_result.html", result)
	else:
		result['msg'] = 'The regist_deal page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


def login(request):
# 登录页面，用户名，密码，（验证码）
# 还差验证码
	result = {}
	if request.method == 'GET':
		return render(request, "login.html")
	else:
		result['msg'] = 'The login page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


def login_deal(request):
# 验证：用户名，密码，验证码
# 验证成功设置cookie（账号直接cookie，密码为md5(密码+log)），并跳转主页，失败则返回登录页面，并在登录页面显示登录失败
# 完成
	result = {}
	if request.method == 'POST':
		try:
			# 验证码
			# code = request.POST['code']
			# if code.lower() != request.session['code'].lower():
			# 	result["msg"] = '验证码错误'
			# 	raise Exception('验证码错误')

			user_name = request.POST['name']
			user_pwd = request.POST['password']

			user = userInfo.objects.filter(user_name=user_name, user_pwd=user_pwd).first()

			if user:
				response = redirect('/index')
				response.set_cookie("name", json.dumps(user_name), 604800)
				response.set_cookie("verify", json.dumps(str(hashlib.md5(bytes(user_pwd + '.log', encoding='utf-8')).hexdigest())), 604800)
				return response
			else:
				# result["status"] = "登录失败"
				# result["code"] = 3
				result["msg"] = "用户名或密码错误"
				return render(request, "login.html", result)

		except Exception as e:
			print("login_deal", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			# result["msg"] = "服务器繁忙"
			return render(request, "login.html", result)				

	else:
		result['msg'] = 'The login_deal page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


def logout(request):
# 注销用户，删除cookie
	if request.method == "GET":
		try:
			response = redirect('/index')
			response.delete_cookie("name")
			response.delete_cookie("verify")
			return response

		except Exception as e:
			#没有cookie信息
			print("logout", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			result["status"] = 0
			return render(request, "index.html", result)

	else:
		result['msg'] = 'The logout page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


def regist_judge(request):
# 返回用户、邮箱判断结果
# 完成
	result = {}
	if request.method == "POST":
		try:
			request_value = request.POST['value']
			request_type = request.POST['type']
			if request_type == "name":
				user = userInfo.objects.filter(user_name=request_value).first()
				result["type"] = "name"
				if user:
					result["status"] = 0
				else:
					result["status"] = 1
				return HttpResponse(json.dumps(result))
			elif request_type == "email":
				user = userInfo.objects.filter(user_email=request_value).first()
				result["type"] = "email"
				if user:
					result["status"] = 0
				else:
					result["status"] = 1
				return HttpResponse(json.dumps(result))
		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("regist_judge", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)
	else:
		result['msg'] = 'The regist_judge page cannot visit by get method.'
		return render(request, "404.html", result, status=404)


def forget(request):
# 忘记密码页面
# 用户名、邮箱
# 验证通过将重新设置密码，不通过则返回该页面
# 完成
	result = {}
	if request.method == "GET":
		return render(request, "forget.html")
	else:
		result['msg'] = 'The forget page cannot visit by post method.'
		return render(request, "404.html", result, status=404)


def forget_deal(request):
# 忘记密码处理逻辑
# 用户名、邮箱
# 验证通过将重新设置密码，不通过则返回该页面
# 完成
	result = {}
	if request.method == "POST":
		#验证成功
		try:
			code = request.POST['code']
			if code.lower() != request.session['code'].lower():
				result["msg"] = '验证码错误'
				raise Exception('验证码错误')

			user_name = request.POST["name"]
			user_email = request.POST["email"]
			user_pwd = request.POST['password']
			user_pwd2 = request.POST['password2']
			if user_pwd != user_pwd2:
				result["msg"] = '两次密码输入不一致'
				raise Exception('两次密码输入不一致')
			if user_name == '' or user_pwd == '' or user_email == '':
				result["msg"] = '数据请勿为空'
				raise Exception('数据请勿为空')
			
			user = userInfo.objects.filter(user_name=user_name, user_email=user_email).first()
			if user:
				user.user_pwd = user_pwd
				user.save()
				result['status'] = "验证成功"
				result['code'] = 1
			else:
				result['status'] = "验证失败"
				result['code'] = 0
			return render(request, "forget_result.html", result)

		except Exception as e:
			result['msg'] = '服务器繁忙'
			print("forget_deal", repr(e), ",wrong_row: ", e.__traceback__.tb_lineno, ", time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  file=open("./error_url_log", "a", encoding="utf-8"))
			return render(request, "404.html", result, status=404)

	else:
		result['msg'] = 'The forget page cannot visit by post method.'
		return render(request, "404.html", result, status=404)	
