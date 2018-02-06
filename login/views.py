from django.shortcuts import render
from django.shortcuts import redirect
from .models import User, ConfirmString
from . import forms
import hashlib
import datetime


# Create your views here.
def hash_code(s, salt='mysite'):  # 加点盐
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())  # update方法只接收bytes类型
    return h.hexdigest()


def send_email(email, code):
    from django.core.mail import EmailMultiAlternatives
    subject = '注册确认邮件'
    text_content = '''感谢注册www.pbh.com，这里是pbh的博客和教程站点，专注于Python和Django技术的分享！\
                        如果你看到这条消息，说明你的邮箱服务器不提供HTML链接功能，请联系管理员！'''
    html_content = '''
                       <p>感谢注册<a href="http://{}/confirm/?code={}" target=blank>www.liujiangblog.com</a>，\
                       这里是pbh的博客和教程站点，专注于Python和Django技术的分享！</p>
                       <p>请点击站点链接完成注册确认！</p>
                       <p>此链接有效期为{}天！</p>
                       '''.format('127.0.0.1:8000', code, 7)
    msg = EmailMultiAlternatives(subject, text_content, '957827348@qq.com', [email])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


def make_confirm_string(user):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.name, now)
    ConfirmString.objects.create(code=code, user=user, )
    return code


def index(request):
    return render(request, 'login/index.html')


def login(request):
    if request.session.get('is_login', None):
        return redirect('/index/')
    if request.method == 'POST':
        login_from = forms.UserForm(request.POST)
        message = "所有字段都必须填写！"
        if login_from.is_valid():
            username = login_from.cleaned_data['username']
            password = login_from.cleaned_data['password']
            try:
                userobject = User.objects.get(name=username)
                if not userobject.has_confirmed:
                    message = '该用户未通过邮件确认!'
                    return render(request, 'login/login.html', locals())
                if userobject.password == password:
                    request.session['is_login'] = True
                    request.session['user_id'] = userobject.id
                    request.session['user_name'] = userobject.name
                    return redirect('/index/')
                else:
                    message = '密码不正确'
            except:
                message = "用户名不存在"
        return render(request, 'login/login.html', locals())
    login_from = forms.UserForm()

    return render(request, 'login/login.html', locals())


def register(request):
    if request.session.get('is_login', None):
        return redirect('/index/')
    if request.method == 'POST':
        register_form = forms.RegisterForm(request.POST)
        message = '请检查填写的内容！'
        if register_form.is_valid():
            username = register_form.cleaned_data['username']
            password1 = register_form.cleaned_data['password1']
            password2 = register_form.cleaned_data['password2']
            email = register_form.cleaned_data['email']
            sex = register_form.cleaned_data['sex']
            if password1 != password2:
                message = '两次输入密码不等'
                return redirect(request, 'login/register.html', locals())
            else:
                same_user_name = User.objects.filter(name=username)
                if same_user_name:
                    message = '用户名已经存在，请重新选择用户名'
                    return redirect(request, 'login/register.html', locals())
                same_email_user = User.objects.filter(email=email)
                if same_email_user:
                    message = '该邮箱已被注册，请选择别的邮箱注册！'
                    return redirect(request, 'login/register.html', locals())
                new_user = User.objects.create()
                new_user.name = username
                new_user.password = password1
                new_user.email = email
                new_user.sex = sex
                new_user.save()
                code = make_confirm_string(new_user)
                send_email(email, code)
                message = '请前往注册邮箱，进行邮件确认！'
                return redirect('/login/')
    register_form = forms.RegisterForm()
    return render(request, 'login/register.html', locals())


def logout(request):
    if not request.session.get('is_login', None):
        return redirect('/index/')
    request.session.flush()
    return redirect('/index/')


def user_confirm(request):
    code = request.GET.get('code', None)
    message = ''
    try:
        confirm = ConfirmString.objects.get(code=code)
    except:
        message = '无效的确认请求!'
        return render(request, 'login/confirm.html', locals())
    c_time = confirm.c_time
    now = datetime.datetime.now()
    if now > c_time + datetime.timedelta(7):
        confirm.user.delete()
        message = '您的邮件已过期，请重新注册！'
        return render(request, 'login/confirm.html', locals())
    else:
        confirm.user.has_confirmed = True
        confirm.user.save()
        confirm.delete()
        message = '感谢您的确认，请使用账户登录'
        return render(request, 'login/confirm.html', locals())
