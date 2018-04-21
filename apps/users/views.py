import re

from django.db.utils import IntegrityError
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.generic import View

from apps.users.models import User


# def register(request):
#     """进入注册界面"""
#     return render(request, 'register.html')


# def do_register(request):
#     """实现注册功能"""
#
#     # 获取post请求参数
#     username = request.POST.get('username')
#     password = request.POST.get('password')
#     password2 = request.POST.get('password2')
#     email = request.POST.get('email')
#     allow = request.POST.get('allow')
#
#     # todo：校验参数合法性
#     # 判断参数不能为空
#     if not all([username, password, password2, email]):
#         return HttpResponse('参数不能为空')
#     # 判断两次密码是否一致
#     if password != password2:
#         return HttpResponse('两次密码不一致')
#     # 判断邮箱合法性
#     if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#         return HttpResponse('邮箱格式不正确')
#     # 判断是否勾选协议，勾选为‘on’
#     if allow != 'on':
#         return HttpResponse('请勾选用户协议')
#
#     # 处理业务：保存用户到数据库表中
#     # django提供的方法，会对密码进行加密
#     try:
#         user = User.objects.create_user(username, email, password)
#         # 修改用户状态为未激活
#         user.is_active = False
#         user.save()
#     except IntegrityError:
#         # 判断用户是否存在
#         return HttpResponse('用户已存在')
#
#     # todo： 发送激活邮件
#
#     return HttpResponse("注册成功，进入登陆页面")


class RegisterView(View):
    """注册视图"""

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 获取post请求参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # todo：校验参数合法性
        # 判断参数不能为空
        if not all([username, password, password2, email]):
            return HttpResponse('参数不能为空')
        # 判断两次密码是否一致
        if password != password2:
            return HttpResponse('两次密码不一致')
        # 判断邮箱合法性
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return HttpResponse('邮箱格式不正确')
        # 判断是否勾选协议，勾选为‘on’
        if allow != 'on':
            return HttpResponse('请勾选用户协议')

        # 处理业务：保存用户到数据库表中
        # django提供的方法，会对密码进行加密
        try:
            user = User.objects.create_user(username, email, password)
            # 修改用户状态为未激活
            user.is_active = False
            user.save()
        except IntegrityError:
            # 判断用户是否存在
            return HttpResponse('用户已存在')

        # todo： 发送激活邮件

        return HttpResponse("注册成功，进入登陆页面")

