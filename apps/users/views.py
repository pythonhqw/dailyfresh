import re

from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired

from apps.users.models import User, Address

from celery_tasks.tasks import send_active_mail
from dailyfresh import settings
from utils.comment import LoginRequiredMixin


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
            user = User.objects.create_user(username, email, password)  # type: User
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
        subject = '天天生鲜激活邮件'  # 主题
        message = ''  # 正文
        from_email = settings.EMAIL_FROM  # 发件人
        recipient_list = [email]  # 收件人
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
            s = TimedJSONWebSignatureSerializer(settings.SECRET_KEY)
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


class LoginView(View):
    """登录类视图"""

    def get(self,request):
        """进入登陆界面"""

        return render(request, 'login.html')

    def post(self, request):

        # 获取请求参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        if remember == 'on':
            # 保存登录状态两周
            request.session.set_expiry(None)
        else:
            # 关闭浏览器就清除cookie
            request.session.set_expiry(0)

        # 校验合法性
        if not all([username, password]):
            return HttpResponse('用户名和密码不能为空')
        # 业务处理：登录
        user = authenticate(username=username, password=password)
        if user is None:
            return HttpResponse('用户名和密码不正确')
        if not user.is_active:
            return HttpResponse('用户名未激活')

        # 登录成功，使用session保存用户登录状态
        login(request, user)

        # 登录成功后要跳转到next指定的界面
        next = request.GET.get("next")
        if next:
            return redirect(next)
        else:
            # 响应请求
            return redirect(reverse('goods:index'))


class LogoutView(View):
    """退出类视图"""

    def get(self, request):
        """注销"""
        # 调用django的logout方法，实现退出，会自动清除用户登录的id
        logout(request)
        return redirect(reverse('goods:index'))


class UserInfoView(LoginRequiredMixin, View):
    """用户信息类视图"""

    def get(self, request):

        # 查询登录用户最新添加的地址，并显示出来
        try:
            # address = Address.objects.filter(user=request.user).order_by('-create_time')[0]
            address = request.user.address_set.latest("create_time")
        except:
            address = None

        context = {
            'tag': 1,
            'address': address,
        }
        return render(request, 'user_center_info.html', context)


class UserOrderView(LoginRequiredMixin, View):
    """用户订单类视图"""

    def get(self, request):
        context = {
            'tag': 2
        }
        return render(request, 'user_center_order.html', context)


class UserAddressView(LoginRequiredMixin, View):
    """用户地址类视图"""

    def get(self, request):

        # 查询登录用户最新添加的地址，并显示出来
        try:
            # address = Address.objects.filter(user=request.user).order_by('-create_time')[0]
            address = request.user.address_set.latest("create_time")
        except:
            address = None

        context = {
            'tag': 3,
            'address': address,
        }
        return render(request, 'user_center_site.html', context)

    def post(self, request):

        # 获取post请求参数
        receiver = request.POST.get('receiver')
        detail = request.POST.get('detail')
        zip_code = request.POST.get('zip_code')
        mobile = request.POST.get('mobile')
        # 参数校验
        if not all([receiver, detail, mobile]):
            return HttpResponse('参数不能为空')
        # 新增一个地址
        Address.objects.create(
            receiver_name=receiver,
            receiver_mobile=mobile,
            detail_addr=detail,
            zip_code=zip_code,
            user=request.user,
        )
        # 添加地址成功，回到当前页面，刷新
        return redirect(reverse('users:address'))



