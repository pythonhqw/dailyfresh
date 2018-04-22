from django.shortcuts import render
from django.http.response import HttpResponse
from django.views.generic import View


class IndexView(View):
    """首页类视图"""

    def get(self, request):

        # django 会自动查询出登录对象，会保存到request对象中
        return render(request, 'index.html')
