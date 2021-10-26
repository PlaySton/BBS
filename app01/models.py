from django.db import models

# Create your models here.


from django.contrib.auth.models import AbstractUser


class UserInfo(AbstractUser):
    phone = models.BigIntegerField(verbose_name='手机号码', null=True)
    avatar = models.FileField(upload_to='avatar/',
                              default='avatar/default.png',
                              verbose_name='用户头像'
                              )
    # 给avatar字段传文件对象,该文件对象会自动存储到avatar文件夹,
    # 如果用户不上传头像,则使用默认头像
    create_time = models.DateField(auto_now_add=True)

    blog = models.OneToOneField('Blog', on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name_plural = '用户表'  # 修改admin后台默认的表名

    def __str__(self):
        return self.username


class Blog(models.Model):
    site_name = models.CharField(max_length=32, verbose_name='站点名称')
    site_title = models.CharField(max_length=32, verbose_name='站点标题')
    # 简单模拟,认识样式的操作的内部原理,本字段存储CSS以及JS样式的路径
    site_theme = models.CharField(max_length=64, verbose_name='站点主题')

    class Meta:
        verbose_name_plural = '站点表'  # 修改admin后台默认的表名

    def __str__(self):
        return self.site_name


class Category(models.Model):
    name = models.CharField(max_length=32, verbose_name='文章分类')
    blog = models.ForeignKey('Blog', on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name_plural = '分类表'  # 修改admin后台默认的表名

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=32, verbose_name='文章标签')
    blog = models.ForeignKey('Blog', on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name_plural = '标签表'  # 修改admin后台默认的表名

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=64, verbose_name='文章标题')
    desc = models.CharField(max_length=255, verbose_name='文章简介')
    # 文章内容有很多,一般情况下都是使用TextField
    content = models.TextField(verbose_name='文章内容')
    create_time = models.DateTimeField(auto_now_add=True)

    # 数据库字段设计优化
    up_num = models.BigIntegerField(default=0, verbose_name='点赞数')
    down_num = models.BigIntegerField(default=0, verbose_name='点踩数')
    comment_num = models.BigIntegerField(default=0, verbose_name='评论数')

    # 外键字段
    blog = models.ForeignKey('Blog', on_delete=models.CASCADE, null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True)
    tags = models.ManyToManyField('Tag',
                                  through='Article2Tag',
                                  through_fields=('article', 'tag'))

    class Meta:
        verbose_name_plural = '文章表'  # 修改admin后台默认的表名

    def __str__(self):
        return self.title


# 创建文章与标签的多对多关系表
class Article2Tag(models.Model):
    article = models.ForeignKey('Article', on_delete=models.CASCADE)
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)


    class Meta:
        verbose_name_plural = '文章标签表'  # 修改admin后台默认的表名


class UpAndDown(models.Model):
    user = models.ForeignKey('UserInfo', on_delete=models.CASCADE)
    article = models.ForeignKey('Article', on_delete=models.CASCADE)
    is_up = models.BooleanField()  # 传布尔值,存0和1

    class Meta:
        verbose_name_plural = '点赞点踩表'  # 修改admin后台默认的表名



class Comment(models.Model):
    user = models.ForeignKey('UserInfo', on_delete=models.CASCADE)
    article = models.ForeignKey('Article', on_delete=models.CASCADE)
    content = models.CharField(max_length=255, verbose_name='评论内容')
    comment_time = models.DateTimeField(auto_now_add=True, verbose_name='评论时间')
    # 自关联,有些评论就是根评论
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True,blank=True)

    class Meta:
        verbose_name_plural = '评论表'  # 修改admin后台默认的表名
