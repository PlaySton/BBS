"""BBS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import re_path
from app01 import views
from django.views.static import serve
from BBS import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', views.register, name='reg'),
    path('login/', views.login, name='login'),

    # 图片验证码相关操作
    path('get_code/', views.get_code, name='get_code'),

    # 首页
    re_path(r'^$', views.home, name='home'),

    # 点赞点踩
    path('up_down/', views.up_down, name='up_down'),
    # 评论
    path('comment/', views.comment, name='comment'),

    # 后台管理
    path('manager/', views.manager, name='manager'),

    # 添加文章
    path('add/article/', views.add_article, name='add_article'),

    # 添加站点
    path('add/sites/', views.add_sites, name='add_sites'),

    # 修改头像
    path('set_avatar/', views.set_avatar, name='set_avatar'),

    # 退出登录
    path('logout/', views.logout, name='logout'),

    # 修改密码
    path('set_password/', views.set_password, name='set_password'),

    # 暴露后端指定文件夹资源
    re_path(r"^media/(?P<path>.*)$", serve, {'document_root': settings.MEDIA_ROOT}),

    # 编辑器上传图片接口
    path('upload_image/', views.upload_image, name='upload_image'),

    # 个人站点页面搭建
    re_path(r'^(?P<username>\w+)/$', views.site, name='site'),

    # 侧边栏的筛选功能
    # re_path(r'^(?P<username>\w+)/category/(\d+)/', views.site, name='site'),
    # re_path(r'^(?P<username>\w+)/tag/(\d+)/', views.site, name='site'),
    # re_path(r'^(?P<username>\w+)/achieve/(\w+)/', views.site, name='site'),
    # 上面的三条url可以合并成一条
    re_path(r'^(?P<username>\w+)/(?P<condition>category|tag|archive)/(?P<param>.*)/', views.site, name='site'),

    # 文章详情页
    re_path(r'^(?P<username>\w+)/article/(?P<article_id>\d+)/', views.article_detail, name='article_detail'),

]
