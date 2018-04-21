from django.shortcuts import render
from django.http.response import HttpResponse


def index(request):
    """首页"""
    return HttpResponse('首页')
