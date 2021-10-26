# 针对用户表的forms组件代码
# 若果自始至终只用到一个forms组件,那么你可以直接建一个py文件书写即可
# 若果你的项目需要多个forms组件,那么可以创建一个文件夹内,根据
# forms组件功能的不通创建不同的py文件

from django import forms
from app01 import models


class MyRegForm(forms.Form):
    username = forms.CharField(label='用户名:',
                               min_length=3,
                               max_length=14,
                               error_messages={
                                   'required': '用户名不能为空',
                                   'min_length': '用户名最少三位',
                                   'max_length': '用户名最多14位',
                               },
                               # 让标签有样式
                               widget=forms.widgets.TextInput(
                                   attrs={'class': 'form-control'})
                               )
    password = forms.CharField(label='密码:',
                               min_length=3,
                               max_length=16,
                               error_messages={
                                   'required': '密码不能为空',
                                   'min_length': '密码最少三位',
                                   'max_length': '密码最多16位',
                               },
                               # 让标签有样式
                               widget=forms.widgets.PasswordInput(
                                   attrs={'class': 'form-control'})
                               )
    confirm_password = forms.CharField(label='确认密码:',
                                       min_length=3,
                                       max_length=16,
                                       error_messages={
                                           'required': '确认密码不能为空',
                                           'min_length': '确认密码最少三位',
                                           'max_length': '确认密码最多16位',
                                       },
                                       # 让标签有样式
                                       widget=forms.widgets.PasswordInput(
                                           attrs={'class': 'form-control'})
                                       )
    email = forms.EmailField(label='邮箱:',
                             error_messages={
                                 'required': '邮箱不能为空',
                                 'invalid': '邮箱格式不正确'
                             },
                             # 让标签有样式
                             widget=forms.widgets.EmailInput(
                                 attrs={'class': 'form-control'})
                             )

    # 钩子函数
    # 局部钩子:校验用户名是否已存在
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # 去数据库中校验
        is_exist = models.UserInfo.objects.filter(username=username)
        if is_exist:
            # 如果存在,提示信息
            self.add_error('username', '用户名已存在!')
        return username

    # 全局钩子
    # 校验两次密码是否一致
    def clean(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if not password == confirm_password:
            self.add_error('confirm_password', '您两次输入的密码不一致,请重新输入')
        return self.cleaned_data
