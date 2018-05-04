from django.conf.urls import url, include

from apps.orders import views

urlpatterns = [

    url(r'^place$', views.PlaceOrderView.as_view(), name='place'),
    # 订单提交
    url(r'^commit$', views.CommitOrderView.as_view(), name='commit'),
    # 支付
    url(r'^pay$', views.OrderPayView.as_view(), name='pay'),
    # 查询支付结果
    url(r'^check$', views.OrderyCheckView.as_view(), name='check'),
]