from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.http.response import HttpResponse
from django.views.generic import View
from django_redis import get_redis_connection
from redis import StrictRedis

from apps.goods.models import GoodsCategory, IndexSlideGoods, IndexPromotion, IndexCategoryGoods, GoodsSKU


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

        # 读取redis中的缓存数据
        context = cache.get('index_page_data')
        if not context:
            print('首页缓存为空,读取数据库数据')
            # 查询首页商品数据：商品类别，轮播图，促销活动
            categories = GoodsCategory.objects.all()
            slide_skus = IndexSlideGoods.objects.all().order_by('index')
            promotions = IndexPromotion.objects.all().order_by('index')[0:2]

            for c in categories:
                # 查询当前类型所有的图片商品和文字商品
                text_skus = IndexCategoryGoods.objects.filter(display_type=0, category=c)
                image_skus = IndexCategoryGoods.objects.filter(display_type=1, category=c)[0:4]
                # 动态给对象新增实例属性
                c.text_skus = text_skus
                c.image_skus = image_skus

            # 定义要缓存的数据
            context = {
                'categories': categories,
                'slide_skus': slide_skus,
                'promotions': promotions,
            }

            # 缓存数据：保存数据到redis中
            # 参数1：键名    参数2：要缓存的数据     参数3：有效期
            cache.set('index_page_data', context, 60*30)
        else:
            print('缓存不为空, 使用缓存')

        # 获取用户添加到购物车商品的总数量
        cart_count = self.get_cart_count(request)
        context.update({'cart_count': cart_count})

        # 响应请求
        # django 会自动查询出登录对象，会保存到request对象中
        return render(request, 'index.html', context)


class DetailView(BaseCartView):
    """商品详情界面"""

    def get(self, request, sku_id):
        """进入商品详情界面"""

        # 要查询数据库的数据
        # 查询商品SKU信息
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 没有查询到跳转到首页
            return redirect(reverse('goods:index'))
        # 查询所有商品分类信息
        categories = GoodsCategory.objects.all()
        # 查询最新商品推荐
        new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[0:2]

        # todo:查询其他规格的商品
        other_skus = GoodsSKU.objects.filter(spu=sku.spu).exclude(id=sku_id)

        # todo:保存用户浏览的商品到redis中
        if request.user.is_authenticated():
            # 获取StrictRedis对象
            strict_redis = get_redis_connection()   # type: StrictRedis
            key = 'history_%s' % request.user.id
            strict_redis.lrem(key, 0, sku_id)
            strict_redis.lpush(key, sku_id)
            strict_redis.ltrim(key, 0, 4)

        # 如果已登录，查询购物车信息
        cart_count = self.get_cart_count(request)
        # 查询其他规格商品

        context = {
            'sku': sku,
            'categories': categories,
            'new_skus': new_skus,
            'cart_count': cart_count,
            'other_skus': other_skus,
        }

        return render(request, 'detail.html', context)


class ListView(BaseCartView):
    """商品列表视图"""

    def get(self, request, category_id, page_num):

        # 获取请求参数
        sort = request.GET.get('sort')

        # 校验参数的合法性
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 查询对应的商品数据
        # 商品分类信息
        categories = GoodsCategory.objects.all()
        # 新品推荐信息（在GoodsSKU表中，查询特定类别信息，按照时间倒序）
        try:
            new_skus = GoodsSKU.objects.filter(category=category).order_by('-create_time')[0:2]
        except:
            new_skus = None
        # 商品列表信息
        if sort == 'price':
            skus = GoodsSKU.objects.filter(category=category).order_by('price')        # 价格排序
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(category=category).order_by('-sales')       # 销量排序
        else:
            skus = GoodsSKU.objects.filter(category=category)                          # 默认排序
            sort = 'default'

        # todo:商品分页信息
        paginator = Paginator(skus, 2)
        try:
            page = paginator.page(page_num)
        except EmptyPage:
            page = paginator.page(1)

        # 购物车信息
        cart_count = self.get_cart_count(request)

        # 定义模板显示的数据
        context = {
            'sort': sort,
            'category': category,
            'categories': categories,
            'new_skus': new_skus,
            # 'skus': skus,
            'cart_count': cart_count,

            'page': page,
            'page_range': paginator.page_range,
        }

        # 响应请求
        return render(request, 'list.html', context)



