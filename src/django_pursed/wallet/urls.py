from django.urls import path

from . import views

app_name = 'wallet'

urlpatterns = [
    path('authorize_purchase_post', views.authorize_purchase_post, name='authorize_purchase_post'),
    path('authorize_purchase_url/<str:encoded>', views.authorize_purchase_url, name='authorize_purchase_url'),
    path('purchase', views.purchase, name='purchase'),
]
