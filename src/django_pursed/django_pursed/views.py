import pickle, base64

import logging
logger = logging.getLogger(__name__)

import django
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.urls.exceptions import NoReverseMatch, Resolver404
from django.conf import settings
from django import forms

from .models import BuyableObject

class ChooseForm(forms.Form):
    description = forms.CharField(label='description',
                                  max_length=300,
                                  help_text='Name of the object that you want to buy')

def index(request):
    if not request.user.is_authenticated:
        chooseform = None
    else:
        chooseform = ChooseForm()
    return render(request, 'index.html', locals())

class Buy(object):
    def __init__(self, buyable, user):
        self.user = user
        self.buyable = buyable
    #
    def __call__(self, *v,**k):
        if self.buyable.owners.filter(username=self.user.username).exists():
            raise Exception( 'User %r already owns %r' % (self.user, self.buyable, ) )
        self.buyable.owners.add(self.user)
        D = { 'return_code' : True,
              'related_object' : self.buyable ,
        }
        return D

def buy(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
    #
    if request.method != 'POST' :
        description = request.GET.get('description','refrigerator')
    else:
        chooseform = ChooseForm(request.POST)
        if not chooseform.is_valid():
            raise SuspiciousOperation('Invalid form')
        description = chooseform.cleaned_data['description']
    try:
        buyable = BuyableObject.objects.filter(description = description).get()
    except BuyableObject.DoesNotExist:
        buyable = BuyableObject(description = description)
        buyable.save()
        logger.warning('Creating BuyableObject %r',buyable)
    #
    from wallet.views import encode_purchase
    purchase_amount = '20'
    description = "buy an object\n of this kind:\n" + description
    x = Buy(buyable=buyable, user=request.user)
    pickled_function = base64.b64encode(pickle.dumps(x)).decode()
    redirect_ok = django.urls.reverse('bought')+'?result=ok'
    redirect_fails =  django.urls.reverse('bought')+'?result=fail'
    encoded = encode_purchase(purchase_amount, description, pickled_function, redirect_ok, redirect_fails)
    #try:
    # in your web site you should use:
    return redirect(django.urls.reverse('wallet:authorize_purchase_url', kwargs={'encoded' : encoded}))
    #except NoReverseMatch:
    #    logger.error('Could not resolve wallet:authorize_purchase_url ')
    #    return redirect('/wallet/authorize_purchase_url/' + encoded)

def bought(request):
    result = request.GET.get('result')
    from wallet.utils import  get_wallet_or_create
    wallet = get_wallet_or_create(request.user)
    return render(request, 'bought.html', locals())
