import re

from django.core.mail import send_mail
from django.db.utils import IntegrityError
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired

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
from celery_tasks.tasks import send_active_mail
from dailyfresh import settings


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
        user = None
        try:
            user = User.objects.create_user(username, email, password)    # type: User
            # 修改用户状态为未激活
            user.is_active = False
            user.save()
        except IntegrityError:
            # 判断用户是否存在
            return HttpResponse('用户已存在')

        # todo： 发送激活邮件
        token = user.generate_active_token()
        # 同步发送会阻塞
        # self.send_active_mail(username, email, token)
        # celery异步发送
        send_active_mail.delay(username, email, token)

        return HttpResponse("注册成功，进入登陆页面")

    @staticmethod
    def send_active_mail(username, email, token):
        """发送激活邮件"""
        subject = '天天生鲜激活邮件'            # 主题
        message = ''                          # 正文
        from_email = settings.EMAIL_FROM      # 发件人
        recipient_list = [email]              # 收件人
        # 带样式的正文
        html_message = ('<h3>尊敬的%s：感谢注册天天生鲜</h3>'
                    '请点击以下链接激活您的帐号:<br/>'
                    '<a href="http://127.0.0.1:8000/users/active/%s">'
                    'http://127.0.0.1:8000/users/active/%s</a>'
                    ) % (username, token, token)

        send_mail(subject, message, from_email, recipient_list, html_message=html_message)


class ActiveView(View):
    """用户激活"""

    def get(self, request, token: str):
        try:
            # 解密 token
            s = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 3600*2)
            # 字符串 转成 bytes
            dict_data = s.loads(token.encode())
        except SignatureExpired:
            # 判断是否失效
            return HttpResponse('激活链接已经失效')

        # 获取用户id
        user_id = dict_data.get('confirm')

        # 修改字段为已激活
        User.objects.filter(id=user_id).update(is_active=True)

        return HttpResponse('激活成功，跳转到登陆界面')


