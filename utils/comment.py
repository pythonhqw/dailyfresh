
from django.contrib.auth.decorators import login_required


# 扩展的一个新功能
class LoginRequiredMixin(object):
    """会做登录检测的类视图"""

    # 需要定义成类方法
    @classmethod
    def as_view(cls, **initkwargs):
        # 视图函数
        view_fun = super().as_view(**initkwargs)
        # 使用装饰器对函数视图进行装饰
        return login_required(view_fun)
