from django.conf.urls import url, include

from apps.users import views

urlpatterns = [
    url(r'^register$', views.register, name="register"),
    url(r'^do_register$', views.do_register, name="do_register"),

]