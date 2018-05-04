from datetime import datetime
from time import sleep

from django.core.urlresolvers import reverse
from django.db import transaction
from django.http.response import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from django_redis import get_redis_connection
from redis import StrictRedis

from apps.goods.models import GoodsSKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import Address
from utils.comment import LoginRequiredMixin


class PlaceOrderView(LoginRequiredMixin, View):

    def post(self, request):

        # 获取请求参数：sku_ids，count
        count = request.POST.get('count')
        sku_ids = request.POST.getlist('sku_ids')

        # 校验参数合法性
        if not sku_ids:
            return redirect(reverse('cart:info'))

        # todo: 查询业务数据： 地址，购物车商品，总数量，总金额
        # 获取用户地址信息
        try:
            # address = Address.objects.filter(user=request.user).order_by('-create_time')[0]
            address = Address.objects.filter(user=request.user).latest('create_time')
        except:
            address = None

        skus = []
        total_count = 0
        total_amount = 0

        strict_redis = get_redis_connection()       # type: StrictRedis
        key = 'cart_%s' % request.user.id
        # 如果是从购物车页面过来，商品的数量从redis中获取
        if count is None:
            # 循环商品id： sku_ids
            for sku_id in sku_ids:
                # 查询商品对象
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except:
                    return redirect(reverse('cart:info'))

                # 获取商品数量和小计金额(类型转换)
                count = strict_redis.hget(key, sku_id)
                count = int(count)
                amount = sku.price * count

                # 动态的给商品对象新增实例属性(count, amount)
                sku.count = count
                sku.amount = amount

                # 添加商品对象到列表中
                skus.append(sku)

                # 累计商品总数量和总金额
                total_count += count
                total_amount += amount
        else:
            # 如果是从详情页面过来，商品的数量从request中获取（只有一个商品）
            sku_id = request.POST.get('sku_ids')

            # 查询商品对象
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except:
                return redirect(reverse('cart:info'))

            # 获取商品数量和小计金额(类型转换)
            count = int(count)
            amount = sku.price * count

            # 判断库存：详情页没有判断库存
            if count > sku.stock:
                return redirect(reverse('goods:detail', args=[sku_id,]))

            # 动态的给商品对象新增实例属性(count, amount)
            sku.count = count
            sku.amount = amount

            # 添加商品对象到列表中
            skus.append(sku)

            # 累计商品总数量和总金额
            total_count += count
            total_amount += amount

            # 将商品数量保存到`Redis`中（以便取消操作在购物车中还能看得到商品）
            strict_redis.hset(key, sku_id, count)

        # 运费(固定)
        trans_cost = 10
        # 实付金额
        totsl_pay = total_amount + trans_cost

        # 定义模板显示的字典数据
        sku_id_str = ','.join(sku_ids)
        context = {
            'skus': skus,
            'address': address,
            'total_count': total_count,
            'total_amount': total_amount,
            'trans_cost': trans_cost,
            'totsl_pay': totsl_pay,
            'sku_id_str': sku_id_str,
        }

        # 响应结果: 返回确认订单html界面
        return render(request, 'place_order.html', context)


class CommitOrderView(View):
    """提交订单"""

    @transaction.atomic
    def post(self, request):

        # 登录判断
        if not request.user.is_authenticated():
            return JsonResponse({'code': 1, 'errmsg': '请先登录'})

        # 获取请求参数：address_id, pay_method, sku_ids_str
        address_id = request.POST.get('address_id')
        pay_method = request.POST.get('pay_method')
        sku_ids_str = request.POST.get('sku_ids_str')

        # 校验参数不能为空
        if not all([address_id, pay_method, sku_ids_str]):
            return JsonResponse({'code': 2, 'errmsg': '参数不能为空'})

        # 判断地址是否存在
        try:
            address = Address.objects.get(id=address_id)
        except:
            return JsonResponse({'code': 3, 'errmsg': '地址不能为空'})

        # 创建保存点
        point = transaction.savepoint()
        try:
            # todo: 修改订单信息表: 保存订单数据到订单信息表中
            total_count = 0
            total_amount = 0
            trans_cost = 10

            order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(request.user.id)
            order = OrderInfo.objects.create(
                order_id=order_id,
                total_count=total_count,
                total_amount=total_amount,
                trans_cost=trans_cost,
                pay_method=pay_method,
                user=request.user,
                address=address,
            )

            # 获取StrictRedis对象: cart_1 = {1: 2, 2: 2}
            strict_redis = get_redis_connection()  # type: StrictRedis
            key = 'cart_%s' % request.user.id
            sku_ids = sku_ids_str.split(',')

            # todo: 核心业务: 遍历每一个商品, 并保存到订单商品表
            for sku_id in sku_ids:
                # 查询订单中的每一个商品对象
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except:
                    # 回滚到保存点，撤销所有的sql操作
                    transaction.savepoint_rollback(point)

                    return JsonResponse({'code': 4, 'errmsg': '商品不存在'})

                # 获取商品数量，并判断库存
                count = strict_redis.hget(key, sku_id)
                count = int(count)
                if count > sku.stock:
                    # 回滚到保存点，撤销所有的sql操作
                    transaction.savepoint_rollback(point)

                    return JsonResponse({'code': 5, 'errmsg': '库存不足'})

                # todo: 修改订单商品表: 保存订单商品到订单商品表
                OrderGoods.objects.create(
                    count=count,
                    price=sku.price,
                    order=order,
                    sku=sku,
                )

                # todo: 修改商品sku表: 减少商品库存, 增加商品销量
                sku.stock -= count
                sku.sales += count
                sku.save()

                # 累加商品数量和总金额
                total_count += count
                total_amount += sku.price * int(count)

                # todo: 修改订单信息表: 修改商品总数量和总金额
            order.total_count = total_count
            order.total_amount = total_amount
            order.save()
        except:
            # 回滚到保存点，撤销所有的sql操作
            transaction.savepoint_rollback(point)

            return JsonResponse({'code': 6, 'errmsg': '创建订单失败'})

        # 提交事务
        transaction.savepoint_commit(point)

        # 从Redis中删除购物车中的商品
        # cart_1 = {1: 2, 2: 2}
        # redis命令: hdel cart_1 1 2
        strict_redis.hdel(key, *sku_ids)

        # 订单创建成功， 响应请求，返回json
        return JsonResponse({'code': 0, 'message': '创建订单成功'})


class OrderPayView(View):

    def post(self, request):
        """支付"""

        if not request.user.is_authenticated():
            return JsonResponse({'code': 1, 'errmsg': '请先登录'})

        # 获取请求参数
        order_id = request.POST.get('order_id')

        if not order_id:
            return JsonResponse({'code': 2, 'errmsg': '参数不能为空'})

        # 查询订单对象
        try:
            order = OrderInfo.objects.get(order_id=order_id, status=1, user=request.user)
        except:
            return JsonResponse({'code': 3, 'errmsg': '无效订单'})

        # 需要支付的总金额
        total_pay = order.total_amount + order.trans_cost

        # todo: 业务逻辑：调用第三方的SDK，实现支付功能
        from alipay import AliPay

        app_private_key_string = open("apps/orders/app_private_key.pem").read()
        alipay_public_key_string = open("apps/orders/alipay_public_key.pem").read()

        # 创建AliPay对象
        alipay = AliPay(
            appid="2016091500513478",   # 沙箱应用id（后期需要换成用户创建的应用id）
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False,True表示使用沙箱环境
        )

        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(total_pay),
            subject='天天生鲜测试订单',
            return_url=None,
            notify_url=None,  # 可选, 不填则使用默认notify url
        )

        # 定义支付引导界面的url
        # 正式环境
        # url = 'https://openapi.alipay.com/gateway.do?' + order_string
        # 沙箱环境: dev
        url = 'https://openapi.alipaydev.com/gateway.do?' + order_string

        return JsonResponse({'code': 0, 'url': url})


class OrderyCheckView(View):

    def post(self, request):
        """查询支付结果"""

        if not request.user.is_authenticated():
            return JsonResponse({'code': 1, 'errmsg': '请先登录'})

        # 获取请求参数
        order_id = request.POST.get('order_id')

        if not order_id:
            return JsonResponse({'code': 2, 'errmsg': '参数不能为空'})

        # 查询订单对象
        try:
            order = OrderInfo.objects.get(order_id=order_id, status=1, user=request.user)
        except:
            return JsonResponse({'code': 3, 'errmsg': '无效订单'})

        # todo: 业务逻辑：调用第三方的SDK，实现支付功能
        from alipay import AliPay

        app_private_key_string = open("apps/orders/app_private_key.pem").read()
        alipay_public_key_string = open("apps/orders/alipay_public_key.pem").read()

        # 创建AliPay对象
        alipay = AliPay(
            appid="2016091500513478",  # 沙箱应用id（后期需要换成用户创建的应用id）
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False,True表示使用沙箱环境
        )

        # todo: 调用第三方的SDK，查询支付结果
        while True:
            dict_data = alipay.api_alipay_trade_query(out_trade_no=order_id)
            code = dict_data.get('code')
            trade_status = dict_data.get('trade_status')
            trade_no = dict_data.get('trade_no')

            if code == '10000' and trade_status == 'TRADE_SUCCESS':
                # 订单支付成功,修改订单状态
                order.status = 4
                order.trade_no = trade_no
                order.save()
                return JsonResponse({'code': 0, 'errmsg': '支付成功'})

            elif (code == '10000' and trade_status == 'WAIT_BUYER_PAY') or code == '40004':
                sleep(2)
                continue

            else:
                # 支付失败
                return JsonResponse({'code': 4, 'errmsg': '支付失败'})




