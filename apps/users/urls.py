from django.conf.urls import url, include

from apps.users import views

urlpatterns = [
    # 视图函数
    # url(r'^register$', views.register, name="register"),
    # url(r'^do_register$', views.do_register, name="do_register"),

    # 类视图        as_view()会返回一个视图函数
    url(r'^register$', views.RegisterView.as_view(), name="register"),

    # 登录
    url(r'^login$', views.LoginView.as_view(), name="login"),
    # 退出
    url(r'^logout$', views.LogoutView.as_view(), name="logout"),

    # 邮件激活
    url(r'^active/(.+)', views.ActiveView.as_view(), name="active"),

    # 用户订单
    url(r'^orders/(\d+)$', views.UserOrderView.as_view(), name="orders"),
    # 用户地址
    url(r'^address$', views.UserAddressView.as_view(), name="address"),
    # 用户信息
    url(r'^$', views.UserInfoView.as_view(), name="info"),



]