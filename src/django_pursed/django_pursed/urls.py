"""django_pursed URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

from django.urls import path, include
from django.contrib import admin

from .views import buy, bought

urlpatterns = [
    path('admin/', admin.site.urls),
    path('buy.html', buy, name='buy'),
    path('bought.html', bought, name='bought'),
    path('wallet/', include('wallet.urls')),
]


#### login, logout

from django.contrib.auth.views import LoginView, LogoutView

urlpatterns += [
    path('accounts/login/',  LoginView.as_view(template_name='admin/login.html',
                                               extra_context={
                                                   'title': 'Login',
                                                   'site_title': 'Django Pursed test site',
                                                   'site_header':  'Django Pursed test site : Login'
                                               },),
         name="my_login", ),
    path('accounts/logout/', LogoutView.as_view(), name="my_logout"),
    ]


