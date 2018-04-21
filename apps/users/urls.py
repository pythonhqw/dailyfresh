from django.conf.urls import url, include

from apps.users import views

urlpatterns = [
    # 视图函数
    # url(r'^register$', views.register, name="register"),
    # url(r'^do_register$', views.do_register, name="do_register"),

    # 类视图        as_view()会返回一个视图函数
    url(r'^register$', views.RegisterView.as_view(), name="register"),

    # 邮件激活
    url(r'^active/(.+)', views.ActiveView.as_view(), name="active"),

]