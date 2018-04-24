from django.shortcuts import render
from django.http.response import HttpResponse
from django.views.generic import View
from django_redis import get_redis_connection
from redis import StrictRedis

from apps.goods.models import GoodsCategory, IndexSlideGoods, IndexPromotion, IndexCategoryGoods


class BaseCartView(View):

    def get_cart_count(self, request):
        """获取购物车中用户的商品总数量"""
        # todo:读取用户添加到购物车的商品总数量
        cart_count = 0  # 购物车商品的总数量
        if request.user.is_authenticated():
            # 已经登录
            strict_redis = get_redis_connection()  # type: StrictRedis
            key = 'cart_%s' % request.user.id
            # 返回　list类型，　元素类型是: bytes
            vals = strict_redis.hvals(key)
            for count in vals:
                cart_count += int(count)
        return cart_count


class IndexView(BaseCartView):
    """首页类视图"""

    def get(self, request):

        # 查询首页商品数据：商品类别，轮播图，促销活动
        categories = GoodsCategory.objects.all()
        slide_skus = IndexSlideGoods.objects.all().order_by('index')
        promotions = IndexPromotion.objects.all().order_by('index')[0:2]

        for c in categories:
            # 查询当前类型所有的图片商品和文字商品
            text_skus = IndexCategoryGoods.objects.filter(display_type=0, category=c)
            image_skus= IndexCategoryGoods.objects.filter(display_type=1, category=c)[0:4]
            # 动态给对象新增实例属性
            c.text_skus = text_skus
            c.image_skus =image_skus

        # 获取用户添加到购物车商品的总数量
        cart_count = self.get_cart_count(request)

        # 定义模板显示的数据
        context = {
            'categories': categories,
            'slide_skus': slide_skus,
            'promotions': promotions,
            'cart_count': cart_count,
        }
        # 响应请求

        # django 会自动查询出登录对象，会保存到request对象中
        return render(request, 'index.html', context)
