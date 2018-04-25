from django.contrib import admin
from django.core.cache import cache

from apps.goods.models import *
from celery_tasks.tasks import *


class BaseAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """后台保存对象数据时使用"""
        super().save_model(request, obj, form, change)
        # 调用celery异步生成静态文件方法
        generate_static_index_page.delay()
        # generate_static_index_page()
        # 修改了数据库数据就需要删除缓存
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        """后台删除对象数据时使用"""
        super().delete_model(request, obj)
        # 调用celery异步生成静态文件方法
        generate_static_index_page.delay()
        # generate_static_index_page()
        # 修改了数据库数据就需要删除缓存
        cache.delete('index_page_data')

class GoodsCategoryAdmin(BaseAdmin):
    pass


class GoodsSPUAdmin(BaseAdmin):
    pass


class GoodsSKUAdmin(BaseAdmin):
    pass


class IndexSlideGoodsAdmin(BaseAdmin):
    pass


class IndexPromotionAdmin(BaseAdmin):
    pass


class IndexCategoryGoodsAdmin(BaseAdmin):
    list_display = ['id']
    pass


admin.site.register(GoodsCategory, GoodsCategoryAdmin)
admin.site.register(GoodsSPU, GoodsSPUAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(IndexSlideGoods, IndexSlideGoodsAdmin)
admin.site.register(IndexPromotion, IndexPromotionAdmin)
admin.site.register(IndexCategoryGoods, IndexCategoryGoodsAdmin)
