import os
from BBS import settings
from django.shortcuts import render, HttpResponse, redirect
from app01.myforms import MyRegForm
from app01 import models
from django.http import JsonResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncMonth
import json
from django.db.models import F
from bs4 import BeautifulSoup
from django.views.decorators.clickjacking import xframe_options_sameorigin


# Create your views here.
def register(request):
    # ajax返回的字典
    back_dic = {'code': 1000, 'msg': ''}
    # 定义一个表单空对象
    form_obj = MyRegForm()
    if request.method == 'POST':

        # 校验数据是否合法
        form_obj = MyRegForm(request.POST)
        # 判断数据是否合法
        if form_obj.is_valid():
            clean_data = form_obj.cleaned_data  # 将校验通过的字典赋值给一个变量
            # 将字典里面的confirm_password键值对删除
            clean_data.pop('confirm_password')
            # 用户头像
            file_obj = request.FILES.get('avatar')
            '''针对用户头像一定要判断是否传值,不能直接添加到字典里去'''
            if file_obj:
                clean_data['avatar'] = file_obj
            # 直接操作数据库保存数据库,**将字典数据打散
            models.UserInfo.objects.create_user(**clean_data)
            back_dic['url'] = '/login/'
        else:
            back_dic['code'] = 2000
            back_dic['msg'] = form_obj.errors
        return JsonResponse(back_dic)
    return render(request, 'register.html', locals())


def login(request):
    if request.method == 'POST':
        back_dic = {'code': 1000, 'msg': ''}
        username = request.POST.get('username')
        password = request.POST.get('password')
        code = request.POST.get('code')
        # 1 先校验验证码是否正确 自己决定是否忽略大小写
        if request.session.get('code').upper() == code.upper():
            # 校验用户名或密码是否正确
            user_obj = auth.authenticate(request, username=username, password=password)
            if user_obj:
                # 保存用户状态
                auth.login(request, user_obj)
                back_dic['url'] = '/home/'
            else:
                back_dic['code'] = 2000
                back_dic['msg'] = '用户名或密码错误'
        else:
            back_dic['code'] = 3000
            back_dic['msg'] = '验证码错误'
        return JsonResponse(back_dic)

    return render(request, 'login.html')


def home(request):
    # 查询本网站所有的文章数据展示到前端页面
    article_queryset = models.Article.objects.all()
    return render(request, 'home.html', locals())


@login_required
def logout(request):
    auth.logout(request)
    return redirect('/home/')


@login_required
def set_password(request):
    if request.is_ajax():
        back_dic = {'code': 1000, 'msg': ''}
        if request.method == 'POST':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            print(old_password)
            print(new_password)
            print(confirm_password)

            # 先校验两次密码是否一致
            if new_password == confirm_password:
                # 校验老密码是否正确
                is_right = request.user.check_password(old_password)
                if is_right:
                    # 修改密码
                    request.user.set_password(new_password)  # 这一步仅仅是在修改对象的属性
                    request.user.save()  # 这一步必不可少,才是真正的操作数据库
                    back_dic['msg'] = '修改成功'
                else:
                    back_dic['code'] = 1001
                    back_dic['msg'] = '两次密码不一致'
            else:
                back_dic['code'] = 1002
                back_dic['msg'] = '原密码错误'
        return JsonResponse(back_dic)


def site(request, username, **kwargs):
    '''

    :param request:
    :param username:
    :param kwargs: 如果该参数有值,也就意味着需要对article_list做额外的筛选工作
    :return:
    '''
    # 校验当前用户名对应的个人站点是否存在
    user_obj = models.UserInfo.objects.filter(username=username).first()
    # 用户如果不存在,返回一个404页面
    if not user_obj:
        return render(request, 'error.html')
    blog = user_obj.blog
    # 查询当前个人站点下的所有文章
    article_list = models.Article.objects.filter(blog=blog)  # queryset对象 侧边栏的筛选其实就是对article_list进一步的筛选
    if kwargs:
        print(kwargs)
        condition = kwargs.get('condition')
        param = kwargs.get('param')
        # 判断用户按那个条件筛选数据
        if condition == 'category':
            article_list = article_list.filter(category_id=param)
        elif condition == 'tag':
            article_list = article_list.filter(tags__id=param)
        else:
            year, month = param.split('-')
            article_list = article_list.filter(create_time__year=year, create_time__month=month)

    # 1.查询当前用户所有的分类及分类下的文章数
    category_list = models.Category.objects.filter(blog=blog).annotate(
        count_num=Count('article__pk')).values_list('name', 'count_num', 'pk')

    # 2.查询当前用户所有的标签及标签下的文章数
    tag_list = models.Tag.objects.filter(blog=blog).annotate(
        count_num=Count('article__pk')).values_list('name', 'count_num', 'pk')

    # 按照年月统计所有的文章
    date_list = models.Article.objects.filter(blog=blog).annotate(
        month=TruncMonth('create_time')).values('month').annotate(
        count_num=Count('pk')).values_list('month', 'count_num')
    return render(request, 'site.html', locals())


def up_down(request):
    '''
    1.校验用户是否登录
    2.判断文章是否当前用户是否自己写的(自己不能给自己点赞)
    3.判断当前是否已经给当前文章点过了,点过了就不能再点
    4.操作数据
    :param request:
    :return:
    '''
    if request.is_ajax():
        back_dic = {'code': 1000, 'msg': ''}
        # 1.判断当前用户是否登录 ,
        # 写代码先把所有正确的逻辑写完再去写错误的逻辑
        # 不要试图两者兼得
        if request.user.is_authenticated:
            article_id = request.POST.get('article_id')
            is_up = request.POST.get('is_up')
            is_up = json.loads(is_up)  # json字符串转换成布尔值
            # 2. 判断当前文章是否是当前文章自己写的
            # 根据文章id查询文章对象,根据文章对象查作者与request.user比对
            article_obj = models.Article.objects.filter(pk=article_id).first()
            if not article_obj.blog.userinfo == request.user:
                # 3.校验当前用户是否已经点了 那个地方记录用户到底点没点
                is_click = models.UpAndDown.objects.filter(user=request.user, article=article_obj)
                if not is_click:
                    # 4.操作数据库记录数据   同步操作普通字段
                    # 判断当前字段是点了赞还是点了踩,从而决定给哪个字段加1
                    if is_up:
                        # 给点赞数加1
                        models.Article.objects.filter(pk=article_id).update(up_num=F('up_num') + 1)
                        back_dic['msg'] = '点赞成功'
                    else:
                        # 给点踩数+1
                        models.Article.objects.filter(pk=article_id).update(down_num=F('up_num') + 1)
                        back_dic['msg'] = '点踩成功'
                    # 操作点赞点踩表
                    models.UpAndDown.objects.create(user=request.user, article=article_obj, is_up=is_up)
                else:
                    back_dic['code'] = 1001
                    back_dic['msg'] = '你已经点过了,不能再点了!'  # 可以做的更加详细,提示用户点了赞还是点了踩
            else:
                back_dic['code'] = 1002
                back_dic['msg'] = '不能给自己点赞'
        else:
            back_dic['code'] = 1003
            back_dic['msg'] = '请先<a href="/login/">登录!</a>'

        return JsonResponse(back_dic)


def article_detail(request, username, article_id):
    '''
    应该先校验username和article_id是否存在,
    但是我们这里先只完成正确情况

    :param request:
    :param username:
    :param article_id:
    :return:
    '''
    user_obj = models.UserInfo.objects.filter(username=username).first()
    blog = user_obj.blog
    # 先获取文章对象
    article_obj = models.Article.objects.filter(pk=article_id, blog__userinfo__username=username).first()
    if not article_obj:
        return render(request, 'error.html')
    # 获取当前文章所有的评论内容
    comment_list = models.Comment.objects.filter(article=article_obj)

    return render(request, 'article_detail.html', locals())


'''
    图片相关的模块
        pip3  install pillow
'''
from PIL import Image, ImageDraw, ImageFont

'''
Image:生成图片
ImageDraw:能够在图片上乱涂乱画
ImageFont:控制字体样式
'''
from io import BytesIO, StringIO

'''
内存管理器模块
BytesIO:临时帮你存储数据,返回的时候数据是二进制
StringIO:临时帮你存储数据,返回的时候数据是字符串
'''
import random


def get_random():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def get_code(request):
    # 推导步骤一:直接获取后端现成的二进制数据发送给前端
    # with open(r'static/img/111.jpg', 'rb', ) as f:
    #     data = f.read()
    # return HttpResponse(data)

    # 推导步骤二:利用pillow模块动态产生图片
    # img_obj = Image.new('RGB', (430, 35), get_random())
    #
    # # 先将图片对象保存起来
    # with open('xxx.png', 'wb') as f:
    #     img_obj.save(f, 'png')
    # # 再讲图片对象读取出来
    # with open('xxx.png', 'rb') as f:
    #     data = f.read()
    # return HttpResponse(data)

    # 推导步骤三:文件存储繁琐,IO效率第 借助于内存管理器模块
    # img_obj = Image.new('RGB', (430, 35), get_random())
    # io_obj = BytesIO()  # 生成一个内存管理对象  你可以看成是文件句柄
    # img_obj.save(io_obj, 'png')
    # return HttpResponse(io_obj.getvalue())
    # 从内存管理器中读取二进制的图片数据返回给前端

    # 推导步骤四:写图片验证码
    img_obj = Image.new('RGB', (430, 35), get_random())
    img_draw = ImageDraw.Draw(img_obj)  # 产生一个画笔对象
    img_font = ImageFont.truetype('static/font/111.ttf', 30)  # 字体样式 大小

    # 随机验证码 五位数的随机验证码 包含 数字 小写字母 大写字母
    code = ''
    for i in range(5):
        random_upper = chr(random.randint(65, 90))
        random_lower = chr(random.randint(97, 122))
        random_int = str(random.randint(0, 9))
        # 从上面三个里面随机选择一个
        tmp = random.choice([random_upper, random_lower, random_int])
        # 将产生的随机字符串写入到图片上
        # 为什么一个个写而不是生成好了在写,一个个写能控制每个字体的间隙,而生成好了就没法控制了
        img_draw.text((i * 65 + 70, 0), tmp, get_random(), img_font)
        # 拼接随机字符串
        code += tmp

    print(code)
    # 随机验证码在登陆的试图函数里要用到,要比对,所以要找地方村其他存起来,并且其他视图函数也能拿到
    request.session['code'] = code
    io_obj = BytesIO()  # 生成一个内存管理对象  你可以看成是文件句柄
    img_obj.save(io_obj, 'png')
    return HttpResponse(io_obj.getvalue())


from django.db import transaction  # 导入事物模块


def comment(request):
    # 自己也可以评论自己的文章
    if request.is_ajax():
        if request.method == 'POST':
            back_dic = {'code': 1000, 'msg': ''}
            if request.user.is_authenticated:
                article_id = request.POST.get('article_id')
                content = request.POST.get('content')
                parent_id = request.POST.get('parent_id')
                # 直接操作评论表存储数据 两张表需要操作
                with transaction.atomic():  # 使用事物功能创建评论
                    models.Article.objects.filter(pk=article_id).update(comment_num=F('comment_num') + 1)
                    models.Comment.objects.create(user=request.user, article_id=article_id, content=content,
                                                  parent_id=parent_id)
                back_dic['msg'] = '评论成功!'
            else:
                back_dic['code'] = 1001
                back_dic['msg'] = '用户未登录!'
            return JsonResponse(back_dic)


from utils.mypage import Pagination


@login_required
def manager(request):
    article_list = models.Article.objects.filter(blog=request.user.blog)
    page_obj = Pagination(current_page=request.GET.get('page', 1), all_count=article_list.count(), per_page_num=10)
    page_queryset = article_list[page_obj.start:page_obj.end]
    return render(request, 'manager/manager.html', locals())


@login_required
def add_article(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get('category')
        tag_id_list = request.POST.getlist('tag')
        blog = request.user.blog
        # 模块使用
        soup = BeautifulSoup(content, 'html.parser')
        tags = soup.find_all()
        # 获取所有的标签
        for tag in tags:
            # print(tag.name) #获取页面所有的标签
            # 针对script 的标签直接删除
            if tag.name == 'script':
                # 删除标签
                tag.decompose()

        # 文章简介
        # 1 先简单暴力的直接切去content150个字符
        # desc = content[0:150]
        # 2 截取文本150个
        desc = soup.text[0:150]
        article_obj = models.Article.objects.create(
            title=title,
            content=str(soup),
            desc=desc,
            category_id=category_id,
            blog=request.user.blog
        )
        # 文章和标签的关系表是我们自己创建的,没法使用add set clear方法
        # 自己取操作关系表 一次性添加多条数据  批量插入bulk_create()
        article_obj_list = []
        for i in tag_id_list:
            tag_article_obj = models.Article2Tag(article=article_obj, tag_id=i)
            article_obj_list.append(tag_article_obj)
        # 批量插入数据
        models.Article2Tag.objects.bulk_create(article_obj_list)
        # 跳转到后台管理文章的展示页
        return redirect('/manager/')

    tag_list = models.Tag.objects.filter(blog=request.user.blog)
    category_list = models.Category.objects.filter(blog=request.user.blog)
    return render(request, 'manager/add_article.html', locals())


def add_sites(request):
    if request.method == 'POST':
        # 添加站点
        site_name = request.POST.get('site_name')
        site_title = request.POST.get('site_title')
        site_css = request.POST.get('site_css')
        # 为用户创建站点
        blog_obj = models.Blog.objects.create(site_name=site_name, site_title=site_title, site_theme=site_css)
        # 为用户绑定站点
        blog_obj.save()
        models.UserInfo.objects.filter(pk=request.user.pk).update(blog_id=blog_obj.pk)
        blog_id = request.user.blog_id
        print(blog_id)
        return redirect('/manager/')

    return render(request, 'manager/add_sites.html', locals())


@xframe_options_sameorigin
def upload_image(request):
    '''
        {
                "error" : 0,
                "url" : "http://www.example.com/path/to/file.ext"
        }
        //失败时
        {
                "error" : 1,
                "message" : "错误信息"
        }
    :param request:
    :return:
    '''
    # 用户写文章上传的图片也算静态资源,也应该放到media文件夹下
    back_dic = {'error': 0, 'url': ''}  # 先提前定义返回给编辑器的数据格式
    if request.method == 'POST':
        # 获取用户上传的图片对象
        file_obj = request.FILES.get('imgFile')
        # 手动拼接存储文件的路径
        file_dir = os.path.join(settings.BASE_DIR, 'media', 'article_img')
        # 优化操作 先判断当前文件夹是否存在,不存在自动创建
        if not os.path.isdir(file_dir):
            os.mkdir(file_dir)  # 创建一层目录结构article_img
        # 拼接图片的完整路径
        file_path = os.path.join(file_dir, file_obj.name)
        with open(file_path, 'wb') as f:
            for line in file_obj:
                f.write(line)
        # 为什么不直接使用file_path ,应为:file_path的地址为:/BBS/media/article/
        back_dic['url'] = '/media/article_img/{}'.format(file_obj.name)
        print(back_dic)

        return JsonResponse(back_dic)


@login_required()
def set_avatar(request):
    if request.method == 'POST':
        file_obj = request.FILES.get('avatar')
        # models.UserInfo.objects.filter(pk=request.user.pk).update(avatar=file_obj) # 不会再自动加avatar前缀
        # 1.自己手动加前缀
        # 2.换一种更新方式
        user_obj = request.user
        user_obj.avatar = file_obj
        user_obj.save()
        return redirect('/home/')
    blog = request.user.blog
    username = request.user.username
    return render(request, 'set_avatar.html', locals())
