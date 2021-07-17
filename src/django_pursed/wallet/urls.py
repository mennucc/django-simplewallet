from django.urls import path

from . import views

app_name = 'wallet'

urlpatterns = [
    ## visualize the contract to the user for authorization, either received by post or by URL
    path('authorize_purchase_post', views.authorize_purchase_post, name='authorize_purchase_post'),
    path('authorize_purchase_encoded_post', views.authorize_purchase_encoded_post, name='authorize_purchase_encoded_post'),
    path('authorize_purchase_url/<str:encoded>', views.authorize_purchase_url, name='authorize_purchase_url'),
    ## effectively proceed with purchase
    path('purchase', views.purchase, name='purchase'),
    ## show wallet
    path('show', views.show, name='show'),
]
